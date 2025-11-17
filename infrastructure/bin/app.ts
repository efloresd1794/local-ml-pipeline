#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MLPipelineStack } from '../lib/ml-pipeline-stack';

const app = new cdk.App();

new MLPipelineStack(app, 'MLPipelineStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT || '000000000000',
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'ML Pipeline with LocalStack - S3, Lambda, and API Gateway',
});

app.synth();
