/**
 * Formats markdown content with consistent styling and structure
 * Handles headers, lists, emphasis, and spacing
 */
export const formatMarkdownContent = (content: string): string => {
  return content
    // Handle headers
    .replace(/^###\s+/gm, '### ')
    .replace(/^(?!###)(\d+)\.\s+\*\*([^*]+)\*\*/g, '### $1. $2\n')
    .replace(/^(?!###)(\d+)\.\s+([^:\n]+):/g, '### $1. $2\n')
    .replace(/#{3,}/g, '###')

    // Handle lists
    .replace(/^(?!\s)-\s+/gm, '* ')
    .replace(/^\s+-\s+/gm, '  * ')
    .replace(/^\*\*([^*]+)\*\*:/gm, '* **$1**:')

    // Handle emphasis
    .replace(/\*\*([^*]+)\*\*/g, (match) => match)
    .replace(
      /(?<!\*)(MODERATE RISK|MODERATELY BULLISH|NEUTRAL TO CAUTIOUSLY BULLISH|HOLD|NEUTRAL TO SLIGHTLY BULLISH|Cautiously Bullish)(?!\*)/g,
      '**$1**'
    )

    // Handle spacing and formatting
    .replace(/###.*\n/g, '$&\n')
    .replace(/\n/g, '  \n')
    .replace(/\*\*([^*\n]+)(?!\*\*)/g, '$1');
}; 