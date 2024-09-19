import 'ol/ol.css'
import Control from 'ol/control/Control'

// Create a custom control class
export class GrowControl extends Control {
  constructor(options = { apiCallback: () => {} }) {
    // Create a button element
    const button = document.createElement('button')
    button.innerHTML = 'G'

    // Create a div wrapper for the button
    const element = document.createElement('div')
    element.className = 'fetch-control ol-unselectable ol-control'
    element.appendChild(button)

    super({
      element: element,
      target: options.target
    })

    // Add click event listener to the button
    button.addEventListener('click', options.apiCallback.bind(this), false)
  }
}
