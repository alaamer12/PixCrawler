import {describe, it, expect} from 'bun:test'
import React from 'react'
import {renderToString} from 'react-dom/server'
import {Logo} from '../components/shared/Logo'

describe('Logo', () => {
  it('renders brand text with correct colors', () => {
    const html = renderToString(<Logo showIcon={false} showText size="md" />)
    expect(html).toContain('Pix')
    expect(html).toContain('Crawler')
    expect(html).toContain('#7096b7')
    expect(html).toContain('#878A8C')
  })

  it('renders icon when showIcon is true', () => {
    const html = renderToString(<Logo showIcon showText={false} size="sm" />)
    expect(html).toContain('PixCrawler logo icon')
  })
})

