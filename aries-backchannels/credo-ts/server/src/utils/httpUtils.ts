import fetch, { RequestInit } from 'node-fetch'

export async function postJson(
  url: string,
  data: Record<string, unknown>,
  options?: Exclude<RequestInit, 'body' | 'method'>
) {
  return await fetch(url, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function get(url: string) {
  return await fetch(url)
}
