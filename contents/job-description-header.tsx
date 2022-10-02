import type { PlasmoContentScript } from "plasmo"
import { withObserver, ATTRIBUTES, CHILD_ADDED, CHARACTER_DATA } from "react-mutation-observer"

export const config: PlasmoContentScript = {
  matches: ["<all_urls>"]
}

console.log("Starting resume-optimizer...")

const Component = withObserver(document)

return (
  <Component
    observedComponent={document}
    onMutation={console.log.bind(null, 'Child addition triggered.')}
    categories={[ATTRIBUTES, CHILD_ADDED, CHARACTER_DATA]}
    subtree={true}
  />
)
