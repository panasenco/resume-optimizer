browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    const result = message.text.padStart(message.amount, message.with);
    sendResponse(result);
});
