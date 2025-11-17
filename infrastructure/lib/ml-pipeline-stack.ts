import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';

export class MLPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Bucket for ML model artifacts
    const modelBucket = new s3.Bucket(this, 'ModelArtifactsBucket', {
      bucketName: 'ml-model-artifacts',
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test only
      autoDeleteObjects: true, // For dev/test only
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // Lambda Layer for ML dependencies (scikit-learn, pandas, numpy, joblib)
    const mlLayer = new lambda.LayerVersion(this, 'MLDependenciesLayer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda-layers/ml-dependencies')),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_9],
      description: 'ML dependencies: scikit-learn, pandas, numpy, joblib',
    });

    // Lambda function for model inference
    const inferenceLambda = new lambda.Function(this, 'InferenceFunction', {
      functionName: 'ml-inference',
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'inference.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../src/lambda')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      layers: [mlLayer],
      environment: {
        MODEL_BUCKET: modelBucket.bucketName,
        MODEL_KEY: 'models/house_price_model.joblib',
        SCALER_KEY: 'models/scaler.joblib',
      },
    });

    // Grant Lambda read access to S3 bucket
    modelBucket.grantRead(inferenceLambda);

    // API Gateway REST API
    const api = new apigateway.RestApi(this, 'MLInferenceAPI', {
      restApiName: 'ML Inference Service',
      description: 'API for ML model inference',
      deployOptions: {
        stageName: 'prod',
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    // Lambda integration
    const lambdaIntegration = new apigateway.LambdaIntegration(inferenceLambda, {
      requestTemplates: { 'application/json': '{ "statusCode": "200" }' },
    });

    // API Routes
    // GET /health - Health check
    const health = api.root.addResource('health');
    health.addMethod('GET', lambdaIntegration);

    // POST /predict - Single prediction
    const predict = api.root.addResource('predict');
    predict.addMethod('POST', lambdaIntegration);

    // POST /predict/confidence - Prediction with confidence interval
    const confidence = predict.addResource('confidence');
    confidence.addMethod('POST', lambdaIntegration);

    // Outputs
    new cdk.CfnOutput(this, 'ModelBucketName', {
      value: modelBucket.bucketName,
      description: 'S3 bucket for ML model artifacts',
      exportName: 'MLModelBucketName',
    });

    new cdk.CfnOutput(this, 'InferenceLambdaArn', {
      value: inferenceLambda.functionArn,
      description: 'ARN of the inference Lambda function',
      exportName: 'MLInferenceLambdaArn',
    });

    new cdk.CfnOutput(this, 'ApiGatewayUrl', {
      value: api.url,
      description: 'API Gateway endpoint URL',
      exportName: 'MLApiGatewayUrl',
    });

    new cdk.CfnOutput(this, 'ApiGatewayId', {
      value: api.restApiId,
      description: 'API Gateway REST API ID',
      exportName: 'MLApiGatewayId',
    });
  }
}
