Subject: Safety evaluation finding in Georgian (ka) for <MODEL>: notice before publication

Hello,

We are running KartuliSafe, an independent evaluation of whether frontier models keep their safety behaviour in
Georgian, a low-resource language with its own script. Method and public material: <REPOSITORY LINK>.

We tested <MODEL> (as served on <DATE RANGE>, model id returned by the API: <ID>) on two published benchmarks,
XSTest and JailbreakBench JBB-Behaviors, in English and in Georgian. The Georgian prompts were reviewed item by item by a
native Georgian linguist. Two automatic judges classified the answers; their reliability in Georgian was measured against
<N> answers labelled by the linguist (agreement <X>).

What we found for <MODEL>:
- Harmful requests answered (full or partial compliance): English <EN %>, Georgian <KA %> (difference <D>, 95% CI <CI>).
- Harmless requests refused: English <EN %>, Georgian <KA %>.
- Harm categories with the largest Georgian gap: <CATEGORIES>.

We plan to publish aggregate results and the Georgian prompts on <DATE = notice + 30 days>. We will never publish
model completions to harmful prompts. We are happy to share the specific prompts and your model's answers privately,
and to consider a short extension if a fix is under way.

Contact: <NAME>, <EMAIL>
