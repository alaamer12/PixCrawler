
import { chromium } from 'playwright';

(async () => {
    console.log('🚀 Launching browser...');
    const browser = await chromium.launch({
        headless: true // Set to false to see the browser UI
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        console.log('📍 Navigating to login page...');
        await page.goto('http://localhost:3000/login');

        // Wait for the form to be ready
        await page.waitForSelector('input[name="email"]');

        console.log('📸 Taking initial screenshot...');
        await page.screenshot({ path: 'login_page_initial.png' });

        console.log('⌨️  Typing credentials...');
        await page.fill('input[name="email"]', 'finaltest@gmail.com');
        await page.fill('input[name="password"]', 'TestPassword123!');

        console.log('🖱️  Clicking sign in...');
        await page.click('button[type="submit"]');

        console.log('⏳ Waiting for navigation...');
        // Wait for URL to change to something other than login
        await page.waitForURL((url) => !url.toString().includes('/login'), { timeout: 10000 });

        console.log(`✅ Navigated to: ${page.url()}`);

        // Wait a bit for the new page to load content
        await page.waitForTimeout(2000);

        console.log('📸 Taking success screenshot...');
        await page.screenshot({ path: 'login_success.png' });

    } catch (error) {
        console.error('❌ Test failed:', error);
        await page.screenshot({ path: 'login_failure.png' });
    } finally {
        await browser.close();
        console.log('👋 Browser closed');
    }
})();
