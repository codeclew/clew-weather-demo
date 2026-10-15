# Real shared-queue source capture

The three Java files are exact, unmodified copies of the queue example in
[mjedynak/concurrency-examples](https://github.com/mjedynak/concurrency-examples)
at commit `a94765fb450bd0f99b6dcabf5bd8f9a8b360be42`.
`upstream-source.json` records their public locations and SHA-256 hashes.

Only the Maven capture build is new: it selects Java release 17 and the three
JDK-only source files. The upstream project declares Java 8 source/target but no
`maven.compiler.release`; the current Codeclew Java admission requires release 17
or newer. This adapter does not reproduce or validate the original full project
build. It does not alter methods, add queue wiring, invent business data, or run
the unbounded producer/consumer application. Original source authorship remains
with the upstream project. Codeclew compiler evidence is scoped to this explicit
Java 17 capture build; runtime scheduling and completion are not established.
