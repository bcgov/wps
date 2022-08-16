import { Control } from 'ol/control'

export class LayerControl extends Control {
  public static buildHFILayerCheckbox(
    labelText: string,
    setShowRawHFI: React.Dispatch<React.SetStateAction<boolean>>,
    checked: boolean
  ) {
    const container = document.createElement('div')
    container.style.display = 'flex'
    container.style.flexDirection = 'row'
    container.style.alignContent = 'center'
    container.style.alignItems = 'center'
    container.style.height = '30px'
    const p = document.createElement('p')
    const strong = document.createElement('strong')
    const label = document.createTextNode(labelText)
    strong.appendChild(label)
    p.appendChild(strong)
    container.appendChild(p)

    const hfiLayerCheckbox = document.createElement('input')
    hfiLayerCheckbox.setAttribute('type', 'checkbox')
    hfiLayerCheckbox.setAttribute('name', labelText)
    hfiLayerCheckbox.id = 'hfi-layer-checkbox'
    hfiLayerCheckbox.title = labelText
    hfiLayerCheckbox.checked = checked
    hfiLayerCheckbox.addEventListener('change', event => {
      const target = event.target as HTMLInputElement
      setShowRawHFI(target.checked)
    })

    const element = document.createElement('div')
    element.style.position = 'relative'
    element.style.padding = '5px'
    element.style.top = '10px'
    element.style.left = '50px'
    element.style.width = '120px'
    element.className = 'ol-selectable ol-control'
    container.appendChild(hfiLayerCheckbox)
    element.append(container)

    hfiLayerCheckbox.addEventListener(
      'click',
      () => {
        console.log('Hello World')
      },
      false
    )

    return new Control({ element })
  }
  // public constructor() {
  //   const hfiLayerCheckbox = document.createElement('input')
  //   const label = document.createTextNode('Raw HFI')
  //   hfiLayerCheckbox.setAttribute('type', 'checkbox')
  //   hfiLayerCheckbox.setAttribute('name', 'Raw HFI')

  //   hfiLayerCheckbox.appendChild(label)
  //   hfiLayerCheckbox.id = 'hfi-layer-checkbox'
  //   hfiLayerCheckbox.title = 'Raw HFI'
  //   hfiLayerCheckbox.checked = false

  //   const element = document.createElement('div')
  //   element.className = 'ol-unselectable ol-control'
  //   element.appendChild(hfiLayerCheckbox)

  //   super({
  //     element: element
  //   })

  //   hfiLayerCheckbox.addEventListener(
  //     'click',
  //     () => {
  //       console.log('Hello World')
  //     },
  //     false
  //   )
  // }
}
