import type { PlasmoContentScript } from "plasmo"

export const config: PlasmoContentScript = {
  matches: ["<all_urls>"]
}

const findIndeedJobDescriptionElement = () => document.getElementById("jobDescriptionText")

const findJobDescriptionElement = findIndeedJobDescriptionElement

const callback = (mutationList, observer) => {
  const jobDescriptionElement = findJobDescriptionElement()
  if (!jobDescription) {
    // Job description element not found, quietly exit
    console.log("Job description element not found")
    return
  }
  var jobDescriptionChanged = false
  for (const mutation of mutationList) {
    if (mutation.target == jobDescriptionElement) {
      console.log("Job description element changed")
      jobDescriptionChanged = true
      break
    } else if (mutation.type === 'childList') {
      for (const addedNode of mutation.addedNodes) {
        if (addedNode == jobDescriptionElement) {
          console.log("Job description element changed")
          jobDescriptionChanged = true
          break
        }
      }
      if (!jobDescriptionChanged) {
        console.log('The job description node was not changed.')
      }
    }
  }
}

const observer = new MutationObserver(callback)

observer.observe(document, { attributes: false, childList: true, subtree: true })

console.log('Started resume-optimizer...')
