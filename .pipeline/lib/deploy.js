"use strict";
const { OpenShiftClientX } = require("pipeline-cli");
const path = require("path");
const debug = require("debug");
const logger = {
  info: debug("info:OpenShiftClient"),
  trace: debug("trace:OpenShiftClient")
};

module.exports = settings => {
  const phases = settings.phases;
  const options = settings.options;
  const phase = options.env;
  const changeId = phases[phase].changeId;
  const oc = new OpenShiftClientX(
    Object.assign({ namespace: phases[phase].namespace }, options)
  );
  const templatesLocalBaseUrl = oc.toFileUrl(
    path.resolve(__dirname, "../../openshift")
  );
  var objects = [];

  // The deployment of your cool app goes here ▼▼▼
  objects.push(
    ...oc.processDeploymentTemplate(
      `${templatesLocalBaseUrl}/deployment.yaml`,
      {
        param: {
          NAME: "wps-web",
          SUFFIX: phases[phase].suffix,
          TAG: phases[phase].tag,
          DOCKER_REGISTRY: `docker-registry.default.svc:5000/${phases[phase].namespace}`
        }
      }
    )
  );
  oc.applyRecommendedLabels(
    objects,
    phases[phase].name,
    phase,
    `${changeId}`,
    phases[phase].instance
  );
  oc.importImageStreams(
    objects,
    phases[phase].tag,
    phases.build.namespace,
    phases.build.tag
  );
  for (let item of objects) {
    if (item.kind == "Deployment") {
      for (let container of item.spec.template.spec.containers) {
        const image = container.image.split("/");
        const imageStreamTagName = `ImageStreamTag/${image[2]}`;
        const imageStreamName = image[2].split(":")[0];
        const newImage = container.image.split("/");
        const imageId = oc
          .raw("get", imageStreamTagName, {
            namespace: image[1],
            output: "custom-columns=IMAGE:.image.metadata.name",
            "no-headers": "true"
          })
          .stdout.trim();
        newImage[2] = `${imageStreamName}@${imageId}`;
        container.image = newImage.join("/");
        logger.info(`Rewriting ${image.join("/")} to ${newImage.join("/")}`);
      }
    }
  }
  oc.applyAndDeploy(objects, phases[phase].instance);
};
