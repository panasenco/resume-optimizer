import { useEffect, useState } from "react"

const jobDescriptionSelectors = ["#jobDescriptionText"];

function getJobDescription() {
  for (let jobDescriptionSelector of jobDescriptionSelectors) {
    var jobDescriptionElement = document.querySelector(jobDescriptionSelector);
    if (jobDescriptionElement) {
      return jobDescriptionElement.innerText;
    }
  }
  return "";
}

function IndexPopup() {
  const [data, setData] = useState({tabUrl: ""})
  
  browser.tabs.query({active: true}).then((tabs) => setData({tabUrl:tabs[0].url}))

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        padding: 16
      }}>
      <h2>Current job description</h2>
      <p>
        {getJobDescription()}
      </p>
    </div>
  )
}

export default IndexPopup
