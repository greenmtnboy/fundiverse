import { _electron as electron } from 'playwright';
import { test, expect, ElectronApplication, Page } from '@playwright/test';

test.describe('Add Connection', async() => {
    let electronApp: ElectronApplication;
    let firstWindow: Page;

    test.beforeAll(async() => {
        electronApp = await electron.launch({ args: ['.']} );
        firstWindow = await electronApp.firstWindow();
    });

    test('Create Portfolio', async() => {
        await firstWindow.title();
        await firstWindow.getByTestId('add-portfolio').click({delay: 1500});
    });

    test('Refresh Portfolio', async() => {
        await firstWindow.title();
        await firstWindow.getByTestId('add-portfolio').click({delay: 1500});
    });

    test.afterAll(async() => {
        await electronApp.close();
    });

});