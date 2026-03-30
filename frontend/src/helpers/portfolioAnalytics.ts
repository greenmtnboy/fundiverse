import {
    useEditorStore,
    useModelConfigStore,
    QueryExecutionService,
} from '@trilogy-data/trilogy-studio-components/stores'
import { DuckDBConnection } from '@trilogy-data/trilogy-studio-components/connections'
import instance from '/src/api/instance'

export async function loadTrilogyModels(
    modelStore: ReturnType<typeof useModelConfigStore>,
    editorStore: ReturnType<typeof useEditorStore>,
    connectionId: string,
    onProgress: (message: string) => void
): Promise<string> {
    onProgress('Loading Trilogy models...')

    const response = await instance.get('trilogy_model')
    const files: Record<string, string> = response.data
    const modelName = 'portfolio'

    let modelConfig = modelStore.models[modelName]
    if (!modelConfig) {
        modelStore.newModelConfig(modelName)
    }
    modelConfig = modelStore.models[modelName]

    Object.entries(files).forEach(([filename, content]) => {
        const editorName = filename
        let editor = editorStore.getEditorByName(editorName)
        console.log('Creating editor for file:', filename)

        if (!editor) {
            editor = editorStore.newEditor(editorName, 'trilogy', connectionId, content)
        } else {
            editor.setContent(content)
        }

        editor.loading = false
        editor.setError(null)
        modelStore.addEditorAsModelSource(modelName, editor)
    })

    onProgress('Trilogy models loaded successfully!')
    return modelName
}

export async function exportPortfolioDatabase(
    portfolioName: string,
    onProgress: (message: string) => void
): Promise<void> {
    onProgress('Exporting portfolio database from backend...')

    try {
        await instance.post(`database/export_portfolio_database`, {
            portfolio_name: portfolioName,
        })
        onProgress('Portfolio database exported successfully!')
    } catch (error: any) {
        console.error('Export failed:', error)
        throw new Error(error.response?.data?.detail || error.message || 'Failed to export portfolio database')
    }
}

export async function loadPortfolioDatabase(
    portfolioName: string,
    connection: DuckDBConnection,
    onProgress: (message: string) => void
): Promise<void> {
    onProgress('Downloading portfolio database...')

    await connection.connect()

    const response = await instance.get(`database/download/${portfolioName}`, {
        responseType: 'blob',
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        },
        // decompress: false, // Disable automatic decompression
        onDownloadProgress: (progressEvent) => {
            if (progressEvent.total) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                onProgress(`Downloading database... ${percentCompleted}%`)
            }
        }
    })

    const dbFile = new File(
        [response.data],
        `${portfolioName}.db`,
        { type: 'application/octet-stream' }
    )

    onProgress('Mounting database to DuckDB...')

    let results = await connection.importFile(dbFile, onProgress)
    console.log(results)
    let useQuery = await connection.query_core(`use ${results.name}; select * from information_schema.tables;`)
    console.log(useQuery)

    let showQuery = await connection.query_core('show databases;')
    console.log('Current tables in the database:', showQuery)

    console.log('Database file imported, verifying tables...')

    onProgress('Database loaded successfully!')

    console.log('Database file imported successfully.')

    await new Promise(resolve => setTimeout(resolve, 500))
}

export async function executePortfolioQuery(
    editorStore: ReturnType<typeof useEditorStore>,
    queryExecutionService: QueryExecutionService,
    connectionId: string,
    editorName: string,
    queryText:string
): Promise<string> {
    let editor = editorStore.getEditorByName(editorName)

    if (!editor) {
        editor = editorStore.newEditor(editorName, 'sql', connectionId, queryText)
    }
    editor.setContent(queryText)

    const editorId = editor.id
    editor.loading = true
    editor.setError(null)

    return new Promise((resolve, reject) => {
        const queryInput = {
            text: editor.contents,
            editorType: 'preql' as const,
            imports: [{
                name: 'entrypoint',
                alias: ''
            }]
        }

        const onProgress = (message: any) => {
            if (message.error) {
                editor.loading = false
                editor.setError(message.message)
            }
            if (message.running) {
                editor.error = null
                editor.loading = true
            }
        }

        const onSuccess = (result: any) => {
            if (result.success && result.results) {
                editorStore.setEditorResults(editorId, result.results)
                editor.loading = false
                resolve(editorId)
            } else if (result.error) {
                editor.setError(result.error)
                editor.loading = false
                reject(new Error(result.error))
            }
        }

        const onError = (error: any) => {
            console.error('Query execution error:', error.message)
            const errorMessage = error.message || 'An error occurred during query execution'
            editor.setError(errorMessage)
            editor.loading = false
            reject(new Error(errorMessage))
        }

        queryExecutionService.executeQuery(
            connectionId,
            queryInput,
            () => { },
            onProgress,
            onError,
            onSuccess
        ).then(({ resultPromise }) => {
            return resultPromise
        }).catch(err => {
            console.error('Query execution failed:', err)
            editor.setError(err.message)
            editor.loading = false
            reject(err)
        })
    })
}
