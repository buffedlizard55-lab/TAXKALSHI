# TAXKALSHI

Sourced research desk for how Kalshi earnings are taxed for a U.S. citizen who is a California resident and who pays tax in the ordinary way, outside withholding and penalty regimes.

The public site is the GitHub Pages build of this repository. Start at `index.html`. The line-by-line record is `data/findings.json`. The critique table is `engine.html`. Irregularities are `flags.html`. The next session’s reading list is `method.html`.

This file is the standing prompt. Read it before changing a conclusion, a rate, or a characterization.

## Standing project prompt

Read this every time work starts, so the desk keeps the same job.

> Review the repo.
>
> Let's create a sliding tax costs for every 10 thousand dollars calculator. It should be able to tell me what the tax is on $10,000, $50,000, all the way up to $200,000.
>
> Let's create a project that investigates how Kalshi earnings are taxed in the US/California as a US American citizen California resident paying taxes normally not subject to any withholding or penalties. Let's focus on obtaining our information from publicly available and trusted verified sources official sources such as the IRS and certified public accountants licensed in California. We should compile enough information and should be able to expand and collect more information when needed and perform proper researching of topics.
>
> Let's answer the following questions and put it into a front page executive summary:
>
> How are Kalshi earnings taxed in California and federal taxes for a normal individual no penalties or withholding.
>
> Research, design, and improve on our project where you see best fit and make those improvements.
>
> The decision making engine of the site should focus on becoming a team of real verified official public accountant with licensing in California and the US that constantly critique each others work to come to the best answer or conclusion.
>
> Work line by line no hallucinations.
>
> Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use. It should solve the problem of having to manually check everything ourselves and having an up to date current feed.
>
> Review the repo.
>
> The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.
>
> Our Core Values
>
> Maximize P(Win)
>
> “Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.
>
> Own the Outcome
>
> We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.
>
> Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.
>
> Verify no hallucinations.
>
> The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.
>
> Site creation
>
> Create a github page for this repo that has clean ui, user friendly, simple and easy to use.
>
> It should be organized and clean. It should include all relevant information in an easy to read format with official verified links as sources for review. Work line by line verify everything no hallucinations.
>
> Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project. It should be worked on in this next session or the next session. Work line by line verify everything no hallucinations.
>
> Run this task through multiple passes.
>
> Pass 1: Implement the task completely and verify the result.
>
> Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.
>
> Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.
>
> Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request. Work line by line verify everything no hallucinations.

## How the core values apply here

Maximize P(Win), for this desk, means maximizing the chance the record is still right when someone checks the link. A decisive 60/40 answer that the IRS has not issued is a loss, even if it looks finished. An empty CPA seat is a win next to a fabricated panel.

Own the outcome means the page, the ledger, the flags, and the validator travel together. A conclusion that is not in `data/findings.json`, or a finding whose quote was not re-read, is unfinished work. Do not hand the gap back to the reader as “consult a professional” and stop. Record the gap, link the page, and leave the next read on `method.html`.

## Rules for the next session

1. Read this prompt before editing.
2. Re-open every URL you rely on. A quote in the ledger is a lead, not a perpetual license to repeat it.
3. Do not add a finding without a quote, a source id, and a why-it-matters line.
4. Do not fill a CPA seat without `license_board_url` and `license_record_date`. The validator rejects a filled license seat that lacks them.
5. Do not state a 2026 California bracket until the Franchise Tax Board publishes the schedule.
6. Do not compute penalties or design withholding. The scope excludes both.
7. Do not treat a missing 1099 as nontaxable income.
8. Run `python3 scripts/validate_ledger.py` before committing a ledger change.
9. Append `data/feed.json` when a source is re-read or a conclusion moves.
10. If a page and the ledger disagree, the ledger wins until the page is corrected. Then they must match.

## What the front page answers

For the scoped person, Kalshi earnings are taxable. Event-contract character is not settled by any IRS ruling located on 24 September 2026. California taxes a resident’s taxable income at ordinary rates and has no lower capital-gains rate. Withholding on contract trading is not described in Kalshi’s tax article. Penalties are out of scope.

That answer is the research posture. It is not a return, not an engagement, and not a ruling.

## Layout

| Path | Role |
| --- | --- |
| `index.html` | Executive summary |
| `calculator.html` | $10,000-step model through $200,000; taxable-income assumptions are explicit |
| `engine.html` | Critique rounds. CPA seats empty until verified |
| `federal.html` | Code and IRS figures, labeled by tax year |
| `california.html` | FTB and Revenue and Taxation Code |
| `reporting.html` | Forms Kalshi describes, and the payment boundary |
| `ledger.html` | Filterable findings |
| `flags.html` | Conflicts and unfinished reads |
| `method.html` | How to extend the feed |
| `data/` | Sources, findings, feed, panel, calculator rate model |
| `scripts/validate_ledger.py` | Structural check, calculator-shape check, not a truth check |

## Check

```bash
python3 scripts/validate_ledger.py
```

The scheduled `Check source links` workflow checks registry reachability weekly and can also be run manually. A reachable URL is not proof that its text or the law is unchanged; a research pass must still re-read and update the dated feed. The `Deploy TAXKALSHI to GitHub Pages` workflow publishes the repository root after a merge to `main`. There is no form for personal tax data.
