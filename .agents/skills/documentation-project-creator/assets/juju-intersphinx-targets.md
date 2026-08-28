# Juju intersphinx targets

This file contains known anchor targets from the [`juju/juju` documentation source](https://github.com/juju/juju/tree/main/docs). Use it to look up the correct intersphinx reference when replacing URL-based links to `documentation.ubuntu.com/juju`.

## URL-to-file mapping

| URL pattern | File location in `juju/juju` |
|---|---|
| `.../en/tutorial/...` | `docs/tutorial/index.md` |
| `.../en/howto/<topic>` | `docs/howto/<topic>.md` |
| `.../en/reference/<topic>` | `docs/reference/<topic>.md` |
| `.../en/reference/juju-cli/list-of-juju-cli-commands/<command>/` | `docs/reference/juju-cli/list-of-juju-cli-commands/<command>.md` |
| `.../en/explanation/<topic>` | `docs/explanation/<topic>.md` |

## Known anchor targets

These are defined at the top of each file as `(<label>)=`. Always verify against the current source if the target is not listed here.

| Topic | File | Anchor target |
|---|---|---|
| Charm (reference) | `docs/reference/charm.md` | `juju:charm` |
| Action | `docs/reference/action.md` | `juju:action` |
| Application | `docs/reference/application.md` | `juju:application` |
| Bundle | `docs/reference/bundle.md` | `juju:bundle` |
| Cloud | `docs/reference/cloud.md` | `juju:cloud` |
| Configuration | `docs/reference/configuration.md` | `juju:configuration` |
| Constraint | `docs/reference/constraint.md` | `juju:constraint` |
| Controller | `docs/reference/controller.md` | `juju:controller` |
| Credential | `docs/reference/credential.md` | `juju:credential` |
| Hook | `docs/reference/hook.md` | `juju:hook` |
| Hook command | `docs/reference/hook-command.md` | `juju:hook-command` |
| Juju CLI | `docs/reference/juju-cli.md` | `juju:juju-cli` |
| Machine | `docs/reference/machine.md` | `juju:machine` |
| Model | `docs/reference/model.md` | `juju:model` |
| Offer | `docs/reference/offer.md` | `juju:offer` |
| Relation | `docs/reference/relation.md` | `juju:relation` |
| Secret | `docs/reference/secret.md` | `juju:secret` |
| Space | `docs/reference/space.md` | `juju:space` |
| Storage | `docs/reference/storage.md` | `juju:storage` |
| Unit | `docs/reference/unit.md` | `juju:unit` |
| User | `docs/reference/user.md` | `juju:user` |
| Juju architecture | `docs/explanation/juju-architecture.md` | `juju:juju-architecture` |
| Juju security | `docs/explanation/juju-security.md` | `juju:juju-security` |
| Tutorial | `docs/tutorial/index.md` | `juju:tutorial` |
| Manage applications | `docs/howto/manage-applications.md` | `juju:manage-applications` |
| Manage actions | `docs/howto/manage-actions.md` | `juju:manage-actions` |
| Manage charms | `docs/howto/manage-charms.md` | `juju:manage-charms` |
| Manage charm resources | `docs/howto/manage-charm-resources.md` | `juju:manage-charm-resources` |
| Manage clouds | `docs/howto/manage-clouds.md` | `juju:manage-clouds` |
| Manage controllers | `docs/howto/manage-controllers.md` | `juju:manage-controllers` |
| Manage credentials | `docs/howto/manage-credentials.md` | `juju:manage-credentials` |
| Manage logs | `docs/howto/manage-logs.md` | `juju:manage-logs` |
| Manage machines | `docs/howto/manage-machines.md` | `juju:manage-machines` |
| Manage metadata | `docs/howto/manage-metadata.md` | `juju:manage-metadata` |
| Manage models | `docs/howto/manage-models.md` | `juju:manage-models` |
| Manage offers | `docs/howto/manage-offers.md` | `juju:manage-offers` |
| Manage relations | `docs/howto/manage-relations.md` | `juju:manage-relations` |
| Manage secret backends | `docs/howto/manage-secret-backends.md` | `juju:manage-secret-backends` |
| Manage secrets | `docs/howto/manage-secrets.md` | `juju:manage-secrets` |
| Manage spaces | `docs/howto/manage-spaces.md` | `juju:manage-spaces` |
| Manage SSH keys | `docs/howto/manage-ssh-keys.md` | `juju:manage-ssh-keys` |
| Manage storage | `docs/howto/manage-storage.md` | `juju:manage-storage` |
| Manage storage pools | `docs/howto/manage-storage-pools.md` | `juju:manage-storage-pools` |
| Manage subnets | `docs/howto/manage-subnets.md` | `juju:manage-subnets` |
| Manage units | `docs/howto/manage-units.md` | `juju:manage-units` |
| Manage users | `docs/howto/manage-users.md` | `juju:manage-users` |

## CLI command targets

Juju CLI command reference pages live at `docs/reference/juju-cli/list-of-juju-cli-commands/<command>.md` in `juju/juju`. Their anchor target follows the pattern `(command-juju-<command>)=`, so the intersphinx reference is `juju:command-juju-<command>`.

**Examples:**

| Command | File | Anchor target |
|---|---|---|
| `juju attach-resource` | `docs/reference/juju-cli/list-of-juju-cli-commands/attach-resource.md` | `juju:command-juju-attach-resource` |
| `juju deploy` | `docs/reference/juju-cli/list-of-juju-cli-commands/deploy.md` | `juju:command-juju-deploy` |
| `juju config` | `docs/reference/juju-cli/list-of-juju-cli-commands/config.md` | `juju:command-juju-config` |
| `juju integrate` | `docs/reference/juju-cli/list-of-juju-cli-commands/integrate.md` | `juju:command-juju-integrate` |

For any other CLI command, apply the `juju:command-juju-<command>` pattern (replacing `<command>` with the command name after `juju `).

> **Note:** If you encounter a URL that maps to a page not listed above, fetch the target file from `juju/juju` and read its anchor label directly. Anchor labels can change; verify against the current source when in doubt.
