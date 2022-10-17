const ambiguity = require("ambiguity");
const BitSet = require("bitset");
const Mark = require("mark.js");
const themes = require("jsonresume-themes");

const utils = require("./utils.js");

function sanitizeSkill(skill) {
  return skill.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
}

class JobDescriptionUpdater {
  constructor(getDescriptionContainer) {
    this._descriptionContainer = null;
    this.optimalResumeJSON = null;
    browser.storage.local.onChanged.addListener(this.optimize.bind(this));
  }
  
  get descriptionContainer() {
    return this._descriptionContainer;
  }
  
  set descriptionContainer(container) {
    this._descriptionContainer = container;
    this.optimize();
    browser.storage.local.get(["theme"]).then((stored) => {
      let optimizerDiv = document.createElement("div");
      let getOptimized = document.createElement("button");
      getOptimized.onclick = () => {
        if (!this.optimalResumeJSON) {
	  alert("ERROR: Optimal resume not computed.\nPlease reload the page and try again.");
	  return;
	}
        let pageContent = themes[stored.theme]({resume: this.optimalResumeJSON});
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
    browser.storage.local.get(["content", "skills"]).then((stored) => {
      // Sanitize each skill using the function from https://stackoverflow.com/a/4371855/12981893
      let sanitizedSkills = stored.skills.map(sanitizeSkill);
      // Create a regex that matches any skill
      let skillRegex = new RegExp("\\b(" + sanitizedSkills.join("|") + ")\\b", 'gi');
      // Populate set of job skills while highlighting them in the job description
      let jobSkillSet = new Set();
      let highlighter = new Mark(this.descriptionContainer);
      highlighter.unmark();
      highlighter.markRegExp(
        skillRegex,
        {
          each: (element) => jobSkillSet.add(element.innerText.toLowerCase()),
	}
      );
      let jobSkills = [...jobSkillSet].sort(utils.skillCompare);
      let sanitizedJobSkills = jobSkills.map(sanitizeSkill)
      let jobSkillRegex = new RegExp("\\b((" + sanitizedJobSkills.join(")|(") + "))\\b", 'gi');
      console.log(jobSkillRegex);
      // Parse the resume template
      let parser = new ambiguity.Parser();
      parser.feed(stored.content);
      let resumeGraph = parser.results[0];
      // Find which job skills are present in each node (not checking across nodes)
      resumeGraph.forEachNode((node, attributes) => {
        let skillVector = new BitSet("0".repeat(jobSkills.length));
        let matches = attributes.text.matchAll(jobSkillRegex);
        if (matches) {
          for (let match of matches) {
            for (let i = 0; i < match.length - 2; i++) {
              if (match[i+2]) {
                skillVector.set(i);
              }
	    }
	  }
	}
	resumeGraph.setNodeAttribute(node, 'skillVector', skillVector);
        console.debug("Node match vector:", attributes.text, skillVector.toString());
      });
      this.optimalResumeJSON = JSON.parse(resumeGraph.pathToString(resumeGraph.randomPath()));
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
