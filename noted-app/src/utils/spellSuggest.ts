// Common English words for predictive spell suggestions
const COMMON_WORDS = [
  'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
  'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
  'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
  'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
  'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
  'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
  'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
  'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
  'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
  'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us',
  'is', 'was', 'are', 'been', 'being', 'has', 'had', 'having', 'does', 'did',
  'doing', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'need',
  'technology', 'computer', 'software', 'hardware', 'data', 'code', 'program',
  'function', 'variable', 'class', 'object', 'array', 'string', 'number', 'boolean',
  'library', 'framework', 'database', 'server', 'client', 'network', 'protocol',
  'algorithm', 'structure', 'design', 'pattern', 'interface', 'module', 'component',
  'system', 'application', 'development', 'testing', 'debugging', 'performance',
  'memory', 'process', 'thread', 'async', 'promise', 'callback', 'event', 'listener',
  'documentation', 'comment', 'bug', 'issue', 'feature', 'release', 'version',
  'important', 'different', 'particular', 'example', 'information', 'something',
  'such', 'same', 'right', 'little', 'great', 'small', 'large', 'high', 'low',
  'same', 'different', 'same', 'too', 'very', 'through', 'where', 'always',
  'never', 'every', 'both', 'each', 'either', 'neither', 'without', 'within',
  'before', 'during', 'while', 'between', 'among', 'under', 'above', 'around',
  'through', 'across', 'along', 'beside', 'behind', 'beyond', 'below', 'beneath',
  'inside', 'outside', 'throughout', 'except', 'besides', 'despite', 'including',
  'excluding', 'regarding', 'concerning', 'according', 'following', 'preceding',
  'original', 'current', 'future', 'past', 'previous', 'next', 'last', 'first',
  'initial', 'final', 'beginning', 'end', 'middle', 'top', 'bottom', 'side'
]

function levenshteinDistance(a: string, b: string): number {
  const aLen = a.length
  const bLen = b.length

  if (aLen === 0) return bLen
  if (bLen === 0) return aLen

  const matrix: number[][] = []

  for (let i = 0; i <= bLen; i++) {
    matrix[i] = [i]
  }

  for (let j = 0; j <= aLen; j++) {
    matrix[0][j] = j
  }

  for (let i = 1; i <= bLen; i++) {
    for (let j = 1; j <= aLen; j++) {
      const cost = a[j - 1] === b[i - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i][j - 1] + 1,      // insertion
        matrix[i - 1][j] + 1,      // deletion
        matrix[i - 1][j - 1] + cost // substitution
      )
    }
  }

  return matrix[bLen][aLen]
}

export function generatePredictiveSuggestions(word: string, maxSuggestions = 2): string[] {
  if (!word || word.length < 2) return []

  const lowerWord = word.toLowerCase()

  // Find words with low edit distance
  const suggestions = COMMON_WORDS
    .map(w => ({
      word: w,
      distance: levenshteinDistance(lowerWord, w)
    }))
    .filter(({ distance }) => distance >= 1 && distance <= 2)
    .sort((a, b) => a.distance - b.distance || b.word.length - a.word.length)
    .slice(0, maxSuggestions)
    .map(({ word: w }) => w)

  return suggestions
}
