var jdContainer = document.getElementById("vjs-container");

var observer = new MutationObserver(
  (mutationList) => {
    var removedNodes = mutationList[0].removedNodes;
    if (removedNodes.length > 0) {
      if (removedNodes[0].id == "vjs-placeholder-container") {
        console.log("Refresh!")
      }
    }
  }
);

observer.observe(jdContainer, {childList: true});
