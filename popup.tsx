import { useEffect, useState } from "react"

function getHello() {
  return "hello";
}

function getTabUrl(tabs) {
  return tabs[0].url;
}

function onError(error) {
  console.error(`Error: ${error}`);
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
      <h2>
        Welcome to your
        <a href="https://www.plasmo.com" target="_blank">
          Plasmo
        </a>{" "}
        Extension!
      </h2>
      <p>
        You're currently on {data.tabUrl}
      </p>
      <a href="https://docs.plasmo.com" target="_blank">
        View Docs
      </a>
    </div>
  )
}

export default IndexPopup
