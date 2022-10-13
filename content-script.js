const themes = require("jsonresume-themes");

const insertOptimizer = (descriptionContainer) => {
  const optimizerDiv = document.createElement("div");
  const getOptimized = document.createElement("button");
  getOptimized.onclick = () => {
    const pageContent = themes.onepage({});
    const pageBlob = new Blob([pageContent], {type: "text/html"});
    const pageURL = URL.createObjectURL(pageBlob);
    window.open(pageURL, "_blank");
  };
  optimizerDiv.appendChild(getOptimized);
  const getOptimizedText = document.createTextNode("Generate HTML");
  getOptimized.appendChild(getOptimizedText);
  descriptionContainer.prepend(optimizerDiv);
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
