### Warmup Rationale

Playing with pinterest, the easiest way to get per-prompt configurable recommendations
was creating boards, so this was the approach I decided to implement for warmup.
Searching alone makes it hard to tailor results beyond just the search results,
and interacting with similar pins outside the board too universally influenced the recommendations
between different prompt requests.

An improvement that I did not get to implement was pre-populating boards with verified images using a combination
of the board creation recommendations on pinterest and the image evaluator logic.

One drawback to this approach comes from edge cases in the pinterest boards system:
-Only one board can be made with a given name (repeat searches can fail) this can be fixed in the future by revisting previous boards if prompts are identical
-Boards will not give recommendations if the names include numbers (tried this as a fix to above), or the names are strange/don't obviously describe an object or aesthetic

These issues are addressable with a more robust playwright bot, but were not within the scope of what is built here.

### Image Eval Rationale

Algorithm and rationale:
1. Split the prompt into adjectives and nouns
- allows us to individually validate the style and object of the prompt
2. Create a prompt for the gpt-4o-mini
- this prompt is used to evaluate the image against the prompt
3. Send the prompt to gpt-4o-mini to score based off both object and style (based off noun and adj keywords)
- the image evaluator returns a score and a description of the image
4. Return the scores and the description
- the scores are floats between 0 and 1
- the description is a string
5. Generate final score as a composite of the object and style scores
-gives control over weighting of content vs style

gpt-4o-mini was selected here for:
1. SOTA image understanding
2. generation speed
3. comparatively low pricing for quality

Prompt engineering improvements could be made to get gpt-4o-mini to more evenly distribute ratings across the 0-1
scale. Most scraped pins are at least of the right object and general style, so compared to a relative baseline of
a completely random image most pins will score generally high for prompts with clear aesthetics.