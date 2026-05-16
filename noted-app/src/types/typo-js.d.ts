declare module 'typo-js' {
  class Typo {
    constructor(lang?: string, affData?: string, dicData?: string)
    check(word: string): boolean
    suggest(word: string): string[]
  }

  export default Typo
}
