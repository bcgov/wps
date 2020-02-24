"use strict";
const { OpenShiftClientX } = require("pipeline-cli");
const path = require("path");

module.exports = settings => {
  const phases = settings.phases;
  const options = settings.options;
  const oc = new OpenShiftClientX(
    Object.assign({ namespace: phases.build.namespace }, options)
  );
  const phase = "build";
  const objects = [];
  const templatesLocalBaseUrl = oc.toFileUrl(
    path.resolve(__dirname, "../../openshift")
  );

  // The building of your cool app goes here ▼▼▼
  objects.push(
    ...oc.processDeploymentTemplate(`${templatesLocalBaseUrl}/build.yaml`, {
      param: {
        SUFFIX: phases[phase].suffix,
        TAG: phases[phase].tag,
        GIT_URL: oc.git.http_url,
        GIT_REF: oc.git.branch.merge
      }
    })
  );
  oc.applyRecommendedLabels(
    objects,
    phases[phase].name,
    phase,
    phases[phase].changeId,
    phases[phase].instance
  );
  oc.applyAndBuild(objects);
};
