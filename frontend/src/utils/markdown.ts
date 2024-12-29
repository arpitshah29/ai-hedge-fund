/**
 * Formats markdown content with consistent styling and structure
 * Handles headers, lists, emphasis, and spacing
 */
export const formatMarkdownContent = (content: string) => {
  // Remove the initial "I'll analyze..." prefix
  const cleanContent = content.replace(/^I'll analyze.*?:\n\n/, '');
  
  // Add special formatting for assessment headers
  return cleanContent
    // Format main headers with emoji indicators
    .replace(/1\. (Market Strength Assessment|Overall Market Sentiment|Overall Technical Analysis|Overall Risk Assessment|Recommended Portfolio Action)/g, 
      '### 📊 $1')
    .replace(/2\. (Notable Patterns|Key Sentiment Indicators|Key Indicator Signals|Key Risk Factors|Position Sizing)/g, 
      '### 🔍 $1')
    .replace(/3\. (Key Factors|24-48 Hour Outlook|Potential Price Action|Risk Mitigation|Risk Management)/g, 
      '### ⚡ $1')
    .replace(/4\. (Trading Recommendations|Position Sizing|Market Outlook)/g, 
      '### 💡 $1')
    
    // Format sub-sections
    .replace(/([a-z]\)) ([A-Z].*$)/gm, '#### 🔸 $2')
    
    // Format key metrics and data points
    .replace(/([\+\-]?\d+\.?\d*%)/g, '`$1`')
    .replace(/\$[\d,\.]+[BM]?/g, '`$&`')
    
    // Format special sections
    .replace(/FOCUS ON:/g, '**Focus Areas:**')
    .replace(/Reasoning:/g, '_Analysis:_')
    .replace(/Key risks:/g, '**Key Risks:**')
    
    // Format bullet sub-lists with better indentation
    .replace(/(\n\s+)\* /g, '$1• ');
}; 