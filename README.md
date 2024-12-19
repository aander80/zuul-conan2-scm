# Demo for SCM issues with Conan 2 in Zuul

This is a quick demo to showcase the issues seen with Conan 2 in [Zuul](https://zuul-ci.org/). In
this demo, Zuul and Gerrit will be set up in a small sandbox in Docker, and a repo containing a
`conanfile.py` (in the same repo as sources) is added to Gerrit as well.

To run the demo, simply run `./demo.sh` (Python3, Docker compose and curl are required). After some
minutes, you should see something along the lines of

```
remote: SUCCESS
remote:
remote:   http://localhost:8080/c/conan-repo/+/2 My change [NEW]
remote:
To http://localhost:8080/a/conan-repo
 * [new reference]   HEAD -> refs/for/master
```

in the output. Click the link. It will run through three pipelines: `check -> gate -> deploy` (this
will again take a couple of minutes). `check` and `gate` should pass, but `deploy` should fail.

## Cloning repos in Zuul

Zuul has a brilliant feature of speculative merging, which allows it to create temporary commits
pre-merge with the contents of what the repo will look like when a change is merged, and will handle
this automatically for multiple changes coming in at the same time (which have no explicit
dependencies toward one another). This is done on the central Zuul executors which communicate with
Ansible remote hosts which run the actual jobs. Because of this structure, the Zuul executors are
pushing the repos to the remote hosts, rather than the remote hosts cloning the repos. As such, the
remote hosts running the jobs (with e.g. Conan) does not have access to the `origin` remote of a
repo.

## Issues with Conan

The problem for us arises when we try to run Conan 2. The suggested way-of-working in the
documentation

```python
def export(self):
    git = Git(self, self.recipe_folder)
    git.coordinates_to_conandata()

def source(self):
    git = Git(self)
    git.checkout_from_conandata_coordinates()
```

we cannot really use in Zuul.

My interpretation of the behavior seen in this demo is that Conan will look and see if any `origin`
refs point to the current commit or a child of it. If not, it will deem that as an unmerged commit
that doesn't exist in `origin` (correct) and will use the local file path to the repo instead.

I imagine this is a bit dangerous if we are for instance building both on Linux and on Windows
concurrently. When exporting the recipe the `conandata.yml` file will be different on Linux and
Windows so the recipe revision will be different. This is what we see in `check` and `gate`, when
running `conan create`.

However, the `deploy` jobs are run after the change is merged, so in that case the commit *does*
exist in `origin` so Conan sets the SCM url to the actual url in `conandata.yml` when exporting the
recipe. Now, since the repo is pushed from the executor to the remote host, we do not have an SSH
key on the remote node and cloning the repo in `source()` will fail.

To see this, click the link with http://localhost:8080/c/conan-repo/+/2 in the output after running
`./demo.sh`. To see the Zuul logs, click the message *Build succeeded* or *Build failed* in the
change log/messages at the bottom of the Gerrit page, to expand it. Click on the link on the same
line as `conan-create` to go to the job. In the Zuul page that opens, click on the *Console* tab to
see all tasks run. Expand *Conan create* and *Print conandata* for seeing the output and the
contents of `conandata.yml` in the cache in the current job.

In Conan 1, we would automatically copy the local repo into the `scm_source` folder in the Conan
cache.

## Fixing this issue

I currently see two possible ways forward.

1.  Add an opt-in feature that allows us to copy the local repo into the Conan cache *consistently*
    and not rely on cloning the repo inside of the Conan cache, which doesn't work for us in Zuul
    and is inefficient since we need to clone the repo once to export the recipe into the cache
    before building with `conan create`. I imagine this would either be something specified in the
    `conanfile.py`, or in the CLI command such as
    `conan create . --export-sources/--export-scm(-sources)`.

2.  Not use `conan create` and build with `conan build` and `conan export-pkg` instead. In that
    case, we could just capture the URL and revision and add that to `conandata.yml` unconditionally
    when exporting to the cache. However, since we are not building inside of the cache it is much
    harder to ensure reproducability, making it harder to switch CI systems seamlessly or for
    developers to build a package locally with a new profile or new dependencies.

A third alternative is to also export the sources with the `exports_sources` attribute. However, for
very large repos we would have to spend a lot of time downloading sources we don't care about if we
do not need to build from sources, or when consumers should not *necessarily* have access to sources
this does not work.
