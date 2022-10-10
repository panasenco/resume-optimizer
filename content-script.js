const insertOptimizer = (descriptionContainer) => {
  const optimizerDiv = document.createElement("div");
  const optimizerContent = document.createTextNode("Optimizer");
  optimizerDiv.appendChild(optimizerContent);
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
