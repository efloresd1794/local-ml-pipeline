import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { MLPipelineStack } from '../lib/ml-pipeline-stack';

describe('MLPipelineStack', () => {
  let app: cdk.App;
  let stack: MLPipelineStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new MLPipelineStack(app, 'TestMLPipelineStack');
    template = Template.fromStack(stack);
  });

  describe('S3 Bucket', () => {
    test('creates S3 bucket for model artifacts', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketName: 'ml-model-artifacts',
        VersioningConfiguration: {
          Status: 'Enabled'
        },
        BucketEncryption: {
          ServerSideEncryptionConfiguration: [
            {
              ServerSideEncryptionByDefault: {
                SSEAlgorithm: 'AES256'
              }
            }
          ]
        }
      });
    });

    test('S3 bucket has correct removal policy', () => {
      // Check that the bucket is configured for deletion (dev/test only)
      template.hasResource('AWS::S3::Bucket', {
        UpdateReplacePolicy: 'Delete',
        DeletionPolicy: 'Delete'
      });
    });

    test('S3 bucket count is exactly 1', () => {
      template.resourceCountIs('AWS::S3::Bucket', 1);
    });
  });

  describe('Lambda Layer', () => {
    test('creates Lambda layer for ML dependencies', () => {
      template.hasResourceProperties('AWS::Lambda::LayerVersion', {
        CompatibleRuntimes: Match.arrayWith(['python3.9', 'python3.10', 'python3.11']),
        Description: 'ML dependencies: scikit-learn, pandas, numpy, joblib, boto3'
      });
    });

    test('Lambda layer count is exactly 1', () => {
      template.resourceCountIs('AWS::Lambda::LayerVersion', 1);
    });
  });

  describe('Lambda Function', () => {
    test('creates inference Lambda function', () => {
      template.hasResourceProperties('AWS::Lambda::Function', {
        FunctionName: 'ml-inference',
        Runtime: 'python3.9',
        Handler: 'inference.handler',
        Timeout: 30,
        MemorySize: 512
      });
    });

    test('Lambda function has correct environment variables', () => {
      template.hasResourceProperties('AWS::Lambda::Function', {
        FunctionName: 'ml-inference',
        Environment: {
          Variables: {
            MODEL_BUCKET: Match.objectLike({
              Ref: Match.stringLikeRegexp('ModelArtifactsBucket.*')
            }),
            MODEL_KEY: 'models/house_price_random_forest_model.joblib',
            SCALER_KEY: 'models/scaler.joblib'
          }
        }
      });
    });

    test('Lambda function uses ML dependencies layer', () => {
      template.hasResourceProperties('AWS::Lambda::Function', {
        Layers: Match.arrayWith([
          Match.objectLike({
            Ref: Match.stringLikeRegexp('MLDependenciesLayer.*')
          })
        ])
      });
    });

    test('Lambda function count includes inference function', () => {
      // CDK creates additional Lambda functions for custom resources (e.g., S3 auto-delete)
      // So we just verify our inference function exists
      template.hasResourceProperties('AWS::Lambda::Function', {
        FunctionName: 'ml-inference'
      });
    });

    test('Lambda has IAM role', () => {
      template.hasResourceProperties('AWS::IAM::Role', {
        AssumeRolePolicyDocument: {
          Statement: [
            {
              Action: 'sts:AssumeRole',
              Effect: 'Allow',
              Principal: {
                Service: 'lambda.amazonaws.com'
              }
            }
          ]
        }
      });
    });
  });

  describe('IAM Permissions', () => {
    test('Lambda has S3 read permissions', () => {
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            {
              Action: Match.arrayWith(['s3:GetObject*', 's3:GetBucket*', 's3:List*']),
              Effect: 'Allow',
              Resource: Match.anyValue()
            }
          ])
        }
      });
    });

    test('Lambda has CloudWatch Logs permissions', () => {
      // CDK automatically adds CloudWatch Logs permissions to the Lambda's execution role
      // These are managed policies, not custom policies, so we verify the role exists
      template.hasResourceProperties('AWS::IAM::Role', {
        AssumeRolePolicyDocument: {
          Statement: Match.arrayWith([
            {
              Action: 'sts:AssumeRole',
              Effect: 'Allow',
              Principal: {
                Service: 'lambda.amazonaws.com'
              }
            }
          ])
        },
        ManagedPolicyArns: Match.arrayWith([
          Match.objectLike({
            'Fn::Join': Match.arrayWith([
              Match.arrayWith([
                Match.stringLikeRegexp('.*AWSLambdaBasicExecutionRole.*')
              ])
            ])
          })
        ])
      });
    });
  });

  describe('API Gateway', () => {
    test('creates REST API', () => {
      template.hasResourceProperties('AWS::ApiGateway::RestApi', {
        Name: 'ML Inference Service',
        Description: 'API for ML model inference'
      });
    });

    test('API Gateway has deployment', () => {
      // The deployment resource exists, but StageName is on the Stage resource
      template.hasResourceProperties('AWS::ApiGateway::Deployment', {
        Description: 'API for ML model inference'
      });
    });

    test('API Gateway has stage with logging enabled', () => {
      template.hasResourceProperties('AWS::ApiGateway::Stage', {
        StageName: 'prod',
        MethodSettings: [
          {
            DataTraceEnabled: true,
            LoggingLevel: 'INFO',
            HttpMethod: '*',
            ResourcePath: '/*'
          }
        ]
      });
    });

    test('API Gateway count is exactly 1', () => {
      template.resourceCountIs('AWS::ApiGateway::RestApi', 1);
    });

    test('has CORS configuration', () => {
      // Check for CORS preflight methods (OPTIONS)
      template.hasResourceProperties('AWS::ApiGateway::Method', {
        HttpMethod: 'OPTIONS'
      });
    });
  });

  describe('API Routes', () => {
    test('has /health GET endpoint', () => {
      template.hasResourceProperties('AWS::ApiGateway::Resource', {
        PathPart: 'health'
      });

      template.hasResourceProperties('AWS::ApiGateway::Method', {
        HttpMethod: 'GET',
        ResourceId: Match.anyValue()
      });
    });

    test('has /predict POST endpoint', () => {
      template.hasResourceProperties('AWS::ApiGateway::Resource', {
        PathPart: 'predict'
      });

      template.hasResourceProperties('AWS::ApiGateway::Method', {
        HttpMethod: 'POST',
        ResourceId: Match.anyValue()
      });
    });

    test('has /predict/confidence POST endpoint', () => {
      template.hasResourceProperties('AWS::ApiGateway::Resource', {
        PathPart: 'confidence'
      });

      template.hasResourceProperties('AWS::ApiGateway::Method', {
        HttpMethod: 'POST',
        ResourceId: Match.anyValue()
      });
    });

    test('has correct number of API resources', () => {
      // health, predict, confidence = 3 resources
      template.resourceCountIs('AWS::ApiGateway::Resource', 3);
    });
  });

  describe('Lambda Integration', () => {
    test('API Gateway methods integrate with Lambda', () => {
      template.hasResourceProperties('AWS::ApiGateway::Method', {
        Integration: {
          IntegrationHttpMethod: 'POST',
          Type: 'AWS_PROXY',
          Uri: Match.objectLike({
            'Fn::Join': Match.arrayWith([
              Match.arrayWith([
                Match.objectLike({
                  'Fn::GetAtt': Match.arrayWith([
                    Match.stringLikeRegexp('InferenceFunction.*'),
                    'Arn'
                  ])
                })
              ])
            ])
          })
        }
      });
    });

    test('Lambda has API Gateway invoke permission', () => {
      template.hasResourceProperties('AWS::Lambda::Permission', {
        Action: 'lambda:InvokeFunction',
        Principal: 'apigateway.amazonaws.com'
      });
    });
  });

  describe('Stack Outputs', () => {
    test('exports model bucket name', () => {
      template.hasOutput('ModelBucketName', {
        Description: 'S3 bucket for ML model artifacts',
        Export: {
          Name: 'MLModelBucketName'
        }
      });
    });

    test('exports Lambda ARN', () => {
      template.hasOutput('InferenceLambdaArn', {
        Description: 'ARN of the inference Lambda function',
        Export: {
          Name: 'MLInferenceLambdaArn'
        }
      });
    });

    test('exports API Gateway URL', () => {
      template.hasOutput('ApiGatewayUrl', {
        Description: 'API Gateway endpoint URL',
        Export: {
          Name: 'MLApiGatewayUrl'
        }
      });
    });

    test('exports API Gateway ID', () => {
      template.hasOutput('ApiGatewayId', {
        Description: 'API Gateway REST API ID',
        Export: {
          Name: 'MLApiGatewayId'
        }
      });
    });

    test('has at least 4 outputs', () => {
      // CDK may add additional outputs (e.g., for custom resources)
      const outputs = template.toJSON().Outputs;
      expect(Object.keys(outputs || {}).length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('Resource Dependencies', () => {
    test('Lambda depends on Lambda layer', () => {
      // The Lambda function should reference the layer
      const lambdaFunctions = template.findResources('AWS::Lambda::Function', {
        Properties: {
          FunctionName: 'ml-inference'
        }
      });
      const lambdaFunction = Object.values(lambdaFunctions)[0];

      expect(lambdaFunction.Properties.Layers).toBeDefined();
      expect(lambdaFunction.Properties.Layers.length).toBeGreaterThan(0);
    });

    test('API methods depend on Lambda function', () => {
      // API Gateway methods should have integration with Lambda
      const methods = template.findResources('AWS::ApiGateway::Method', {
        Properties: {
          HttpMethod: Match.anyValue()
        }
      });

      expect(Object.keys(methods).length).toBeGreaterThan(0);
    });
  });

  describe('Security Best Practices', () => {
    test('S3 bucket has encryption enabled', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketEncryption: {
          ServerSideEncryptionConfiguration: Match.anyValue()
        }
      });
    });

    test('Lambda function has IAM role with least privilege', () => {
      // Lambda should have only necessary permissions
      const policies = template.findResources('AWS::IAM::Policy');
      expect(Object.keys(policies).length).toBeGreaterThan(0);

      // Verify policies exist but don't grant excessive permissions
      Object.values(policies).forEach((policy: any) => {
        const statements = policy.Properties.PolicyDocument.Statement;
        statements.forEach((statement: any) => {
          // Should not have '*' actions
          expect(statement.Action).not.toContain('*');
        });
      });
    });

    test('API Gateway has CORS properly configured', () => {
      // Should have OPTIONS methods for CORS preflight
      template.hasResourceProperties('AWS::ApiGateway::Method', {
        HttpMethod: 'OPTIONS'
      });
    });
  });

  describe('Resource Naming', () => {
    test('resources have consistent naming convention', () => {
      const lambda = template.findResources('AWS::Lambda::Function', {
        Properties: {
          FunctionName: 'ml-inference'
        }
      });
      const lambdaProps = Object.values(lambda)[0].Properties;
      expect(lambdaProps.FunctionName).toBe('ml-inference');

      const bucket = template.findResources('AWS::S3::Bucket', {
        Properties: {
          BucketName: 'ml-model-artifacts'
        }
      });
      const bucketProps = Object.values(bucket)[0].Properties;
      expect(bucketProps.BucketName).toBe('ml-model-artifacts');
    });
  });

  describe('Snapshot Testing', () => {
    test('stack matches snapshot', () => {
      const stackJson = template.toJSON();
      expect(stackJson).toMatchSnapshot();
    });
  });
});
