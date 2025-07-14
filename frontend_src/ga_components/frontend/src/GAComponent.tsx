import React, { useEffect } from "react"
import { withStreamlitConnection, Streamlit } from "streamlit-component-lib"

interface Props {
  args: { measurementId: string }
}

const GAComponent = ({ args }: Props) => {
  const { measurementId } = args

  useEffect(() => {
    if (document.getElementById("ga-script")) return

    const script = document.createElement("script")
    script.id = "ga-script"
    script.async = true
    script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`
    document.head.appendChild(script)

    const inlineScript = document.createElement("script")
    inlineScript.innerHTML = `
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', '${measurementId}');
    `
    document.head.appendChild(inlineScript)

    console.log("GA script injected with ID:", measurementId)

    Streamlit.setComponentValue("GA initialized")
  }, [measurementId])

  return null
}

export default withStreamlitConnection(GAComponent)
