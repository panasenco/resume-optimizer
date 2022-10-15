const ambiguity = require("ambiguity");
const Mark = require("mark.js");
const skills = require("./skills.json");
const themes = require("jsonresume-themes");

// Should probably move all this into a background script after all...
// Sort skills in order of descending length to capture "Data Warehousing" before "Data"
sortedSkills = skills.sort((s1,s2) => s2.length - s1.length);
// Sanitize each skill using the function from https://stackoverflow.com/a/4371855/12981893
sanitizedSkills = sortedSkills.map((s) => s.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&'));
// Create a regex that matches any skill
skillRegex = new RegExp("\\b(" + sanitizedSkills.join("|") + ")\\b", 'g');
// Can now find all matches with something like Array.from(str.matchAll(skillRegex))


const insertOptimizer = (descriptionContainer) => {
  try {
    const highlighter = new Mark(descriptionContainer);
    highlighter.markRegExp(skillRegex);
    const optimizerDiv = document.createElement("div");
    const getOptimized = document.createElement("button");
    getOptimized.onclick = () => {
      browser.storage.local.get().then((stored) => {
        const parser = new ambiguity.Parser();
        parser.feed(stored.content);
        resumeGraph = parser.results[0];
        const randomJSON = resumeGraph.pathToString(resumeGraph.randomPath());
        const pageContent = themes[stored.theme]({resume: JSON.parse(randomJSON)});
        const pageBlob = new Blob([pageContent], {type: "text/html"});
        const pageURL = URL.createObjectURL(pageBlob);
        window.open(pageURL, "_blank");
      });
    };
    optimizerDiv.appendChild(getOptimized);
    const getOptimizedText = document.createTextNode("Generate HTML");
    getOptimized.appendChild(getOptimizedText);
    descriptionContainer.prepend(optimizerDiv);
  } catch (e) {
    console.error(e);
  }
}

var jobContainer = document.getElementById("vjs-container");

var refreshObserver = new MutationObserver(
  (mutationList) => {
    var removedNodes = mutationList[0].removedNodes;
    if (removedNodes.length > 0) {
      if (removedNodes[0].id == "vjs-placeholder-container") {
        var jobFrame = document.getElementById("vjs-container-iframe");
        var descriptionContainer = jobFrame.contentWindow.document.getElementById("jobDescriptionText");
        insertOptimizer(descriptionContainer);
      }
    }
  }
);

refreshObserver.observe(jobContainer, {childList: true});
