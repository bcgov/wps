import React, { useRef, useEffect } from 'react'

interface CanvasProps {
  width: number
  height: number
}

const Canvas = ({ width, height }: CanvasProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (canvasRef.current) {
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      if (ctx) {
        // const id = ctx.createImageData(1, height)
        // id.data[0] = 0xff
        // id.data[1] = 0x00
        // id.data[2] = 0x00
        // id.data[3] = 0xff
        // ctx.putImageData(id, 0, 0)

        for (let x = 0; x < width; ++x) {
          const ros = (100 / width) * x
          const r = 0xff
          const g = Math.max(0, 255 - (ros / 100) * 255)
          const b = 0x00
          const a = 0xff
          ctx.fillStyle = 'rgba(' + r + ',' + g + ',' + b + ',' + a / 255 + ')'
          ctx.fillRect(x, 0, 1, height)
        }

        // context.moveTo(0, 0)
        // context.lineTo(0, height)
        // context.stroke()
        // context.beginPath()
        // context.arc(50, 50, 50, 0, 2 * Math.PI)
        // context.fill()
      }
    }
  }, [width, height])

  return <canvas ref={canvasRef} height={height} width={width} />
}

Canvas.defaultProps = {
  width: window.innerWidth,
  height: window.innerHeight
}

export default Canvas
