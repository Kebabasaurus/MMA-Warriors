# Multi-Sport Combat Universe

## Design Document

## Vision

The Multi-Sport Combat Universe expands the game beyond MMA into a
living combat sports ecosystem.

The objective is **not** to create multiple management games. Instead,
the additional sports exist to enrich the MMA world by creating
believable champions, prospects and crossover athletes with genuine
histories.

The player still spends almost all of their time managing an MMA
promotion.

------------------------------------------------------------------------

# Design Principles

-   Keep management focused on MMA.
-   Simulate other sports efficiently.
-   Share one athlete-generation pipeline.
-   Allow rare but meaningful crossover.
-   Preserve separate histories, champions and records.
-   Let every sport develop its own legends.

------------------------------------------------------------------------

# Supported Sports

-   MMA
-   Boxing
-   Kickboxing
-   Muay Thai
-   Wrestling
-   Brazilian Jiu-Jitsu (BJJ)

Future sports (Judo, Sambo, Karate etc.) can be added using the same
architecture.

------------------------------------------------------------------------

# World Structure

Each sport initially has one AI-controlled flagship promotion.

Each maintains its own:

-   Rankings
-   Champions
-   Events
-   Records
-   Awards
-   Hall of Fame
-   Media

The sports exist independently while sharing the same world.

------------------------------------------------------------------------

# Shared Athlete Generation

Every combat athlete is generated once.

The generator determines:

-   Nationality
-   Region
-   Physical profile
-   Personality
-   Potential
-   Preferred combat background
-   Career goals

The simulation then chooses the sport that best fits the athlete.

Examples:

  Athlete                   Starting Sport
  ------------------------- ----------------
  Elite boxer               Boxing
  Elite wrestler            Wrestling
  Elite BJJ specialist      BJJ
  Elite Muay Thai striker   Muay Thai
  Balanced athlete          MMA

------------------------------------------------------------------------

# MMA Athlete Philosophy

Unlike the other sports, MMA should **not** generate only well-rounded
fighters.

MMA is a ruleset, not a fighting style.

Most MMA fighters are competent everywhere, but every generation should
contain specialists and outliers.

Examples include:

-   Elite wrestlers
-   Submission specialists
-   Heavy-handed knockout artists
-   Technical kickboxers
-   Pressure fighters
-   Counter strikers
-   Clinch specialists
-   Ground-and-pound specialists
-   Complete mixed martial artists

Every MMA fighter should receive a primary archetype that influences:

-   Initial attribute weighting
-   AI fight style
-   Commentary
-   Media descriptions
-   Development priorities

Exceptional specialists should occasionally appear, creating memorable
careers and stylistic matchups.

As careers progress, fighters naturally evolve through training,
coaching and experience.

------------------------------------------------------------------------

# Shared Career Systems

Every athlete shares:

-   Ageing
-   Development
-   Injuries
-   Personality
-   Career goals
-   Popularity
-   Media
-   Retirement

Only competition rules and attribute weighting differ between sports.

------------------------------------------------------------------------

# Sport Weighting

Each discipline favours different skills.

-   Boxing → Punching, footwork, timing.
-   Kickboxing → Punches, kicks, movement.
-   Muay Thai → Kicks, knees, elbows, clinch.
-   Wrestling → Takedowns, control, balance.
-   BJJ → Submissions, control, transitions.
-   MMA → Wide variety of archetypes rather than one balanced template.

------------------------------------------------------------------------

# Lightweight AI Simulation

Each non-MMA sport runs efficiently.

Every season the AI:

-   Books events
-   Updates rankings
-   Crowns champions
-   Develops prospects
-   Retires veterans
-   Generates media stories

Detailed fight simulation is unnecessary.

------------------------------------------------------------------------

# Athlete Migration

Most athletes remain in their primary discipline.

Occasionally they may:

-   Join MMA
-   Accept crossover bouts
-   Return to a previous sport
-   Retire

Migration depends on:

-   Personality
-   Age
-   Financial opportunity
-   Legacy goals
-   Skill suitability
-   Interest from promotions

Rare crossover keeps these moments exciting.

------------------------------------------------------------------------

# Player-Owned Divisions

Players cannot manage existing AI promotions in other sports.

Instead they may create divisions beneath their MMA promotion, such as:

-   Boxing
-   Kickboxing
-   Muay Thai
-   Wrestling
-   BJJ

Shared:

-   Budget
-   Brand
-   Staff
-   Sponsorship
-   Media

Separate:

-   Roster
-   Champions
-   Rankings
-   Events
-   Records
-   Awards

------------------------------------------------------------------------

# Separate Records

Each discipline tracks independent careers.

Example:

-   MMA: 18--2
-   Boxing: 5--1
-   BJJ: 22--6

Achievements never overwrite one another.

------------------------------------------------------------------------

# Commentary & Media

The media recognises crossover stars.

Examples:

-   Former Boxing World Champion makes MMA debut.
-   Olympic wrestler signs with an MMA promotion.
-   BJJ legend enters professional MMA.

------------------------------------------------------------------------

# Long-Term Goal

The combat sports world should feel connected.

Players should naturally encounter stories such as:

-   An Olympic wrestler becoming an MMA legend.
-   A Muay Thai superstar moving to MMA.
-   A BJJ icon remaining loyal to grappling.
-   An ageing boxer attempting one final crossover.

The additional sports exist to support and enrich the MMA experience,
creating a living world with believable careers, histories and legends.
