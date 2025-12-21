/// A simplified version of `best_of.projects_collection.categorize_projects`.
///
/// Returns categories with `projects` and `hidden-projects` populated.
///
/// Note that the number of projects (including hidden ones) in the output might less than that of the input, because deleted projects will be dropped.
#let categorize-projects(projects, categories) = {
  // We can't `let … = categories.at(…)` here, or the variable `categories` won't be updated.

  for id in categories.keys() {
    categories.at(id).insert("projects", ())
    categories.at(id).insert("hidden-projects", ())
  }

  for p in projects {
    if p.homepage == "{}" and not p.show and p.github_id != none and p.github_url == none {
      // This is a deleted GitHub repo. Drop it.
      continue
    }

    if p.show {
      categories.at(p.category).projects.push(p)
    } else {
      categories.at(p.category).hidden-projects.push(p)
    }
  }

  categories
}
