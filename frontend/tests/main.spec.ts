import { _electron as electron } from 'playwright';
import { test, expect, ElectronApplication, Page } from '@playwright/test';

test.describe('Add Connection', async() => {
    let electronApp: ElectronApplication;
    let firstWindow: Page;

    test.beforeAll(async() => {
        electronApp = await electron.launch({ args: ['.']} );
        firstWindow = await electronApp.firstWindow();
    });

    test('Create and Delete Portfolio', async() => {
        await firstWindow.title();
        await firstWindow.getByTestId('add-portfolio').click({delay: 500})  
        // const popup = await firstWindow.waitForEvent('popup');
        const newPortfolioInput = await firstWindow.locator("#input-add-portfolio-name");
        await newPortfolioInput.click();
        await newPortfolioInput.pressSequentially('ci-port');
        await firstWindow.getByTestId('btn-add-portfolio-submit').click({delay: 500});
        await firstWindow.getByTestId('cmp-port-ci-port');
        await firstWindow.getByTestId('btn-del-ci-port').click({delay: 500});
        await firstWindow.getByTestId('btn-del-ci-port-confirm').click({delay: 500});
        await expect(firstWindow.getByTestId('cmp-port-ci-port')).toHaveCount(0);
    });


    test.afterAll(async() => {
        await electronApp.close();
    });

});