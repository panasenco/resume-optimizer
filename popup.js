const resumeContent = document.getElementById("resume-content");
const resumeTheme = document.getElementById("resume-theme");

document.getElementById("optimizer-form").addEventListener("submit", (e) => {
  e.preventDefault();
  console.log("Saving resume content:", resumeContent.value, "and theme:", resumeTheme.value);
  let sendingMessage = browser.runtime.sendMessage({
      content: resumeContent.value,
      theme: resumeTheme.value,
  });
  sendingMessage.then((result) => {
    console.log("Success:", result);
  });
}, false);

document.getElementById("copy-to-clipboard").addEventListener("click", (e) => {
  console.log("TODO copy to clipboard");
});
