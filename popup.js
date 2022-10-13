const resumeContent = document.getElementById("resume-content");
const resumeTheme = document.getElementById("resume-theme");

browser.storage.local.get().then((stored) => {
  resumeContent.value = stored.content;
  resumeTheme.value = stored.theme;
});

document.getElementById("optimizer-form").addEventListener("submit", (e) => {
  e.preventDefault();
  console.log("Saving resume content:", resumeContent.value, "and theme:", resumeTheme.value);
  browser.storage.local.set({
      content: resumeContent.value,
      theme: resumeTheme.value,
  });
}, false);

document.getElementById("copy-to-clipboard").addEventListener("click", (e) => {
  e.preventDefault();
  navigator.clipboard.writeText(resumeContent.value);
});
