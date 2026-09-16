#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.infra_stack import BattleLensStack

app = cdk.App()

BattleLensStack(
    app,
    "BattleLensStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
