import React from "react"
import { createRoot } from "react-dom/client"
import MyGAComponent from "./GAComponent"

const container = document.getElementById("root")
if (container) {
  const root = createRoot(container)
  root.render(
    <React.StrictMode>
      <MyGAComponent />
    </React.StrictMode>
  )
}
