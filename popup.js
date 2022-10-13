const resumeContent = document.getElementById("resume-content");

document.getElementById("optimizer-form").addEventListener("submit", (e) => {
    e.preventDefault();
    console.log("Saving resume content:", resumeContent.value);
}, false);

document.getElementById("copy-to-clipboard").addEventListener("click", (e) => {
    console.log("TODO copy to clipboard");
});
