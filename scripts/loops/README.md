# Loops Scripts

## Commands

Run the full bootstrap:

```bash
bash scripts/loops/bootstrap.sh
```

Check skills only:

```bash
bash scripts/loops/check-skills.sh
```

## Files

- `skills.manifest.json`：项目 skills 清单。
- `check-skills.sh`：检查本地 skills 状态。
- `bootstrap.sh`：打印 Loops 入口并运行检查。

## Notes

- Scripts do not install external dependencies.
- Scripts do not modify global Trae configuration.
- Missing project-specific skills are reported as `required-custom`.
