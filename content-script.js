const ambiguity = require("ambiguity");
const Mark = require("mark.js");
const themes = require("jsonresume-themes");

class JobDescriptionUpdater {
  constructor(getDescriptionContainer) {
    this._descriptionContainer = null;
    browser.storage.local.onChanged.addListener(this.optimize.bind(this));
  }
  
  get descriptionContainer() {
    return this._descriptionContainer;
  }
  
  set descriptionContainer(container) {
    this._descriptionContainer = container;
    this.optimize();
    browser.storage.local.get(["content", "theme"]).then((stored) => {
      let optimizerDiv = document.createElement("div");
      let getOptimized = document.createElement("button");
      getOptimized.onclick = () => {
        let parser = new ambiguity.Parser();
        parser.feed(stored.content);
        let resumeGraph = parser.results[0];
        let randomJSON = resumeGraph.pathToString(resumeGraph.randomPath());
        let pageContent = themes[stored.theme]({resume: JSON.parse(randomJSON)});
        let pageBlob = new Blob([pageContent], {type: "text/html"});
        let pageURL = URL.createObjectURL(pageBlob);
        window.open(pageURL, "_blank");
      };
      optimizerDiv.appendChild(getOptimized);
      let getOptimizedText = document.createTextNode("Generate HTML");
      getOptimized.appendChild(getOptimizedText);
      container.prepend(optimizerDiv);
    });
  }
  
  optimize() {
    if (!this.descriptionContainer) {
      console.warn("JobDescriptionUpdater.optimize() called but no descriptionContainer defined yet - ignoring...");
      return;
    }
    browser.storage.local.get(["skills"]).then((stored) => {
      // Sanitize each skill using the function from https://stackoverflow.com/a/4371855/12981893
      const sanitizedSkills = stored.skills.map((s) => s.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&'));
      // Create a regex that matches any skill
      const skillRegex = new RegExp("\\b(" + sanitizedSkills.join("|") + ")\\b", 'gi');
      // Can now find all matches with something like Array.from(str.matchAll(skillRegex))
      const highlighter = new Mark(this.descriptionContainer);
      highlighter.unmark();
      highlighter.markRegExp(skillRegex);
    });
  }
}

const updater = new JobDescriptionUpdater();

// Listen for changes to Indeed's job container (if found on this page)
const indeedJobContainer = document.getElementById("vjs-container");
if (indeedJobContainer) {
  const indeedRefreshObserver = new MutationObserver(
    (mutationList) => {
      let removedNodes = mutationList[0].removedNodes;
      if (removedNodes.length > 0) {
        if (removedNodes[0].id == "vjs-placeholder-container") {
          let jobFrame = document.getElementById("vjs-container-iframe");
          updater.descriptionContainer = jobFrame.contentWindow.document.getElementById("jobDescriptionText");
        }
      }
    }
  );
  indeedRefreshObserver.observe(indeedJobContainer, {childList: true});
}
