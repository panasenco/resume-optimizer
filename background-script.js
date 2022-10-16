browser.storage.local.get().then((stored) => { 
  let updateContent = false;
  if (!stored.content) {
    stored.content = require("./sample-resume.json.ambiguity");
    updateContent = true;
  }
  if (!stored.skills) {
    stored.skills = require("./skills.json");
    updateContent = true;
  }
  if (!stored.theme) {
    stored.theme = "onepage";
    updateContent = true;
  }
  if (updateContent) {
    browser.storage.local.set(stored);
  }
});


browser.menus.create(
  {
    id: "toggle-skill",
    title: "&Toggle Skills List Membership",
    contexts: ["selection"],
  },
  () => void browser.runtime.lastError,
);

browser.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "toggle-skill") {
    console.log(info);
  }
});
