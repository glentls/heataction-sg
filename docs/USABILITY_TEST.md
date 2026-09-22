# Coordinator usability test protocol

This is a task-based test protocol for a prospective coordinator, written so someone other than
the people who built the app can administer it. **It has not yet been run with a real coordinator.**
An engineering walkthrough of these same tasks is recorded in STATUS.md, confirming each task is
mechanically completable without errors; that is not a substitute for this test. Only a naive
first-time user can reveal genuine confusion, hesitation, or misreadings, and none of this
project's team can play that role credibly for their own interface.

## Before you start

- Run the synthetic demo (`python -m heataction demo` then `python -m heataction serve`) so the
  session is reproducible and no real data is at risk. Open http://127.0.0.1:8000.
- Sit with the participant; do not explain the interface first. Read each task aloud, then stay
  quiet and let them work. Note where they hesitate, misclick, or ask a question.
- For each task, record: completed unaided / completed with a hint / not completed; time taken;
  and anything they said or did that surprised you.
- Afterward, ask the two open questions at the end.

## Tasks

1. **Reduce team capacity.** "Your team lost a volunteer. You now only have one team slot instead
   of two. Change the settings so the app reflects that, and tell me which area no longer gets a
   team." *Success:* changes the budget field and correctly names the area that drops out.

2. **Explain a recommendation.** "Your supervisor asks why one of the recommended areas was
   chosen. Find out why, in the app, and explain it to me in your own words." *Success:* locates
   the explanation for a specific area and can paraphrase the heat/demographic reasoning without
   reading it verbatim.

3. **Lock a commitment.** "One of the areas already has a home visit scheduled today regardless of
   the weather. Make sure the app keeps recommending a team for that area even if the budget drops,
   and record why." *Success:* locks the area with a nonempty reason, then confirms (e.g. by
   lowering the budget) that it still shows as assigned.

4. **Compare team sizes.** "Your manager is deciding whether to ask for one more team. Find out
   what would change if you had one extra team slot, and tell me which area would gain support."
   *Success:* uses the scenario comparison to correctly name the area that gains a slot.

5. **Check how fresh the weather data is.** "Before committing a team to an area, check how
   recent its weather reading is and whether it's been trending up or down." *Success:* finds the
   weather-history chart for the right station and states both the trend direction and the age of
   the latest reading.

6. **Hand off the plan.** "You need to share today's plan with the field team, who aren't at a
   computer with this app open." *Success:* exports the CSV and can say where the downloaded file
   went.

## After the tasks

- "What, if anything, was confusing or took longer than it should have?"
- "Is there anything you expected the app to do that it didn't?"

## Recording results

Add a dated entry to STATUS.md after a real session: who ran it (role, not necessarily name),
which tasks were completed unaided/with a hint/not at all, approximate times, and direct quotes
for anything surprising. Do not average task outcomes into a single "usability score" — with one
or two participants that number would imply more precision than the data supports.
