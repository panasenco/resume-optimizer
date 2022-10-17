const resumeContent = document.getElementById("resume-content");
const resumeTheme = document.getElementById("resume-theme");

browser.storage.local.get().then((stored) => {
  resumeContent.value = stored.content;
  resumeTheme.value = stored.theme;
});

document.getElementById("optimizer-form").addEventListener("submit", (e) => {
  e.preventDefault();
  browser.storage.local.set({
      content: resumeContent.value,
      theme: resumeTheme.value,
  });
}, false);

document.getElementById("template-to-clipboard").addEventListener("click", (e) => {
  e.preventDefault();
  navigator.clipboard.writeText(resumeContent.value);
});

document.getElementById("skills-to-clipboard").addEventListener("click", (e) => {
  e.preventDefault();
  browser.storage.local.get(["skills"]).then((stored) => {
    navigator.clipboard.writeText(JSON.stringify(stored.skills, null, "\n").replace(/\n\n/g,"\n"));
  });
});
