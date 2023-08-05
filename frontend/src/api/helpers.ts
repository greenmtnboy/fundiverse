import axios from 'axios';

const axiosHelpers = {

    getErrorMessage(error: Error) {
        if (axios.isAxiosError(error)) {
            if (error.response) {
                return error.response.data;
            }
            return error.message
        }
        else { return error.message }
    }
};


export default axiosHelpers;