const binarySearch = require("binary-search");

// Compare skills first in order of decreasing length and then alphabetically
function skillCompare(skill0, skill1) {
  let lengthDiff = skill1.length - skill0.length;
  return lengthDiff == 0 ? skill0.localeCompare(skill1) : lengthDiff;
}

// Set default values for stored data if they don't exist
browser.storage.local.get().then((stored) => { 
  let updateContent = false;
  if (!stored.content) {
    stored.content = require("./sample-resume.json.ambiguity");
    updateContent = true;
  }
  if (!stored.skills) {
    stored.skills = require("./sorted-skills.json");
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

// Create context menu item, preventing errors if it's already defined
browser.menus.create(
  {
    id: "toggle-skill",
    title: "&Toggle Skills List Membership",
    contexts: ["selection"],
  },
  () => void browser.runtime.lastError,
);

// Handle context menu click
browser.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "toggle-skill") {
    let skill = info.selectionText.trim().toLowerCase();
    browser.storage.local.get(["skills"]).then((stored) => { 
      memberIndex = binarySearch(stored.skills, skill, skillCompare);
      if (memberIndex >= 0) {
        // Skill already present, delete it from the array
        stored.skills.splice(memberIndex, 1);
        console.debug(`Deleted skill ${skill} at index ${memberIndex}. New context: ${stored.skills.slice(memberIndex-3, memberIndex+4)}`);
      } else {
        // Skill not yet present, insert it
        stored.skills.splice(-memberIndex - 1, 0, skill);
        console.debug(`Inserted skill ${skill} at index ${-memberIndex - 1}. New context: ${stored.skills.slice(-memberIndex-4, -memberIndex+3)}`);
      }
      browser.storage.local.set(stored);
    });
  }
});
