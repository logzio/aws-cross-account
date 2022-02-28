# aws-cross-account

This integration allows sending your AWS logs from multiple AWS accounts to Logz.io.

**Note:** this integration is relevant to [services that publish their logs to Cloudwatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/aws-services-sending-logs.html).

## Architecture overview

<< TODO - FLOW CHART >>

At a high level, this integration creates the following:

**In the landing account:**
1. Kinesis stream, that receives logs from multiple accounts.
2. Destination, that encapsulates the stream and allows sending the logs into it.
3. Lambda function, that uses the Kinesis stream as a trigger, and sends the logs into Logz.io
4. More Destinations (upon demand) for each region you need to ship logs from.

**In the sending accounts:**
1. Subscription filters, that send the logs from Cloudwatch into the Destination in the landing account.

## Setting up the landing account

The landing account is the account that will receive the logs from your multiple AWS accounts, and will send them to Logz.io.

### Create a main stack

Select the button below to create a new stack dedicated to receiving logs into a Kinesis stream, then send them to Logz.io with a Lambda function.

| AWS Region | Launch a stack                                                                                                                                                                                                                                                                                     |
| --- |----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `us-east-1` | [![Deploy to AWS](https://dytvr9ot2sszz.cloudfront.net/logz-docs/lights/LightS-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=aws-cross-account-main&templateURL=https://integrations-testing.s3.amazonaws.com/cross-accounts/0.0.1/sam-template-main.yaml) |

#### Step 1 - Specify template

Keep the default setting in the **Create stack** screen and select **Next**.

<< TODO - SCREENSHOT >>

#### Step 2 - Specify stack details

Specify the stack details as per the table below and select **Next**.

| Parameter                | Description                                                                                                                                                                                                                                                                                             | Required / Defaults |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|
| `LogzioREGION`           | Two-letter region code, or blank for US East (Northern Virginia). This determines your listener URL (where you're shipping the logs to) and API URL. You can find your region code in the Regions and URLs [here](https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls table). | Default: `us`       |
| `LogzioTOKEN`            | The token of the account you want to ship to. Can be found [here](https://app.logz.io/#/dashboard/settings/general).                                                                                                                                                                                    | Required            | 
| `LogzioCOMPRESS`         | If true, the Lambda will send compressed logs. If false, the Lambda will send uncompressed logs.                                                                                                                                                                                                        | Default: `false`    |
| `KinesisStreamBatchSize` | The largest number of records that will be read from your stream at once.                                                                                                                                                                                                                               | Default: `100`      |
| `AccountsArns`           | Comma-delimited list (**no spaces**) of ARNs of the landing account, and the accounts you'd like to send logs from. The ARNs should be in the format: arn:aws:logs:*:<<ACCOUNT_NUMBER>>:*                                                                                                               | Required            |
| `SendingAccounts`        | Comma-delimited list (**no spaces**) of the sending accounts numbers. Each account should be under double quotes: "1234","5678","9012"                                                                                                                                                                  | Requiered           |

<< TODO - SCREENSHOT >>

#### Step 3 - Configure stack options

Specify the **Key** and **Value** parameters for the **Tags** (optional) and select Next.

<< TODO - SCREENSHOT >>

#### Step 4 - Review

Confirm that you acknowledge that AWS CloudFormation might create IAM resources and select Create stack.

<< TODO - SCREENSHOT >>

#### Wait for stack to create

Wait a few minutes for the stack to create. After creation some outputs will be available on the stack's **Outputs** tab. You'll need some of the outputs when configuring the sending accounts, and when creating more Destinations.

<< TODO - SCREENSHOT >>

#### Important notes for landing account:
1. This stack creates (among other things) a Destination in the region you chose to deploy, meaning that you will be able to send logs from that region only. You'll need to have in your sending account a Destination in every region you'd want to send logs from. To deploy more destinations see [this section](<<TODO>>).
2. See [this section](<<TODO>>) for instructions on how to add more accounts **after** you deployed your main stack.


### Create Destination stacks

You'll need to set up a destination on each region you'll want to send logs from (in your landing account).
Follow these instructions to setup a cloudformation stack that will deploy the Destination.

Select the button below to create a new stack.

| AWS Region | Launch a stack                                                                                                                                                                                                                                                                                            |
| --- |-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `us-east-1` | [![Deploy to AWS](https://dytvr9ot2sszz.cloudfront.net/logz-docs/lights/LightS-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=aws-cross-account-destination&templateURL=https://integrations-testing.s3.amazonaws.com/cross-accounts/0.0.1/sam-template-destination.yaml) |

#### Step 1 - Specify template

Keep the default setting in the **Create stack** screen and select **Next**.

<< TODO - SCREENSHOT >>

#### Step 2 - Specify stack details

Specify the stack details as per the table below and select **Next**.

**Note:** all parameters are required.

| Parameter          | Description                                                                                                                                                 |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `RoleArn`          | The ARN of the Role you've created in your main stack. You can find it in the main stack's Outputs tab, under LogzioCrossAccountRole                        |
| `KinesisStreamArn` | The ARN of the Kinesis Stream you've created in your main stack. You can find it in the main stack's Outputs tab, under LogzioCrossAccountKinesisStreamArn. |
| `SendingAccounts`  | Comma-delimited list (**no spaces**) of the sending accounts numbers. Each account should be under double quotes: "1234","5678","9012"                      |

<< TODO - SCREENSHOT >>

#### Step 3 - Configure stack options

Specify the **Key** and **Value** parameters for the **Tags** (optional) and select Next.

<< TODO - SCREENSHOT >>

#### Step 4 - Review

Confirm that you acknowledge that AWS CloudFormation might create IAM resources and select Create stack.

<< TODO - SCREENSHOT >>

#### Wait for stack to create

Wait a few minutes for the stack to create. After creation some outputs will be available on the stack's **Outputs** tab. You'll need some of the outputs when configuring the sending accounts.

<< TODO - SCREENSHOT >>


## Setting up the sending accounts

**Note:** You'll need to repeat the following steps for each service want to send logs from.

### Prerequisites:

* Your service [publishes logs to Cloudwatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/aws-services-sending-logs.html). 
* Your log group is in the format: `/<<AWS-PARTITION/<<SERVICE-NAME>>/<<LOG-GROUP-NAME>>`, for example: `/aws/lambda/my_function`.

You can create your subscription filter with one of the following:
* AWS CLI
* Terraform

### Create a subscription filter with AWS CLI:

#### Step 1 - connect to AWS

Make sure your AWS CLI is connected to the account you want to send logs from, and you're configured to the region you want to send logs from.

#### Step 2 - create Subscription Filter

In your terminal, insert the following command, with changes where applicable:

```shell
aws logs put-subscription-filter \
    --log-group-name "<<LOG-GROUP-NAME>>" \
    --filter-name "<<SUBSCRIPTION-FILTER-NAME>>" \
    --filter-pattern " " \
    --destination-arn "<<DESTINATION-ARN>>"
```

| Parameter                      | Description                                                                                                                                                                                                                    |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `<<LOG-GROUP-NAME>>`           | The log group you want to collect logs from.                                                                                                                                                                                   |
| `<<SUBSCRIPTION-FILTER-NAME>>` | Name for the subscription filter you create.                                                                                                                                                                                   |
| `<<DESTINATION-ARN>>`          | ARN of the Destination you created in the landing account. If you created your with our Cloudformation Stack, you can find the ARN in the Stack's Outputs tab. The Destination should be in the same region as your log group. |

### Create a subscription filter with Terraform:

**Note:** These instructions assume that you are familiar with Terraform and the AWS Provider.

In your Terraform configuration, add the following:

```tf
resource "aws_cloudwatch_log_subscription_filter" "subscription_filter" {
  name            = "<<SUBSCRIPTION-FILTER-NAME>>"
  log_group_name  = "<<LOG-GROUP-NAME>>"
  filter_pattern  = " "
  destination_arn = "<<DESTINATION-ARN>>"
}
```

| Parameter                      | Description                                                                                                                                                                                                                    |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `<<LOG-GROUP-NAME>>`           | The log group you want to collect logs from.                                                                                                                                                                                   |
| `<<SUBSCRIPTION-FILTER-NAME>>` | Name for the subscription filter you create.                                                                                                                                                                                   |
| `<<DESTINATION-ARN>>`          | ARN of the Destination you created in the landing account. If you created your with our Cloudformation Stack, you can find the ARN in the Stack's Outputs tab. The Destination should be in the same region as your log group. |

**Tip:** if you're creating the log group and the subscription filter at the same time, add to the subscription filter a `depends_on` field, and make it dependent on the log group, so that the log group will be created first.

## Adding new accounts after deployment

If you wish to add more accounts to send from, after you already deployed your stacks:

### Update main stack:

In your AWS Console, go to Cloudformation and choose your main stack.
Then, click on **Update**.

#### Step 1 - Specify template

Choose **Use current template** and click on **Next**.

<< TODO - SCREENSHOT >>

#### Step 2 - Specify stack details

Update the parameters `AccountsArns`, and `SendingAccounts` with the accounts you want to add (don't override the existing values, add your new accounts to the lists).
Click **Next** when you're done.

<< TODO - SCREENSHOT >>

#### Steps 3 - 4:

Click on next in steps 3-4, and check the acknowledgment checkbox, and click on **Update stack**.

<< TODO - SCREENSHOTS >>

#### Wait for the stack to be updated

### Update Destinations stacks:

If you created Destination stacks, you'll need to update them as well, and add the new account numbers as well.

Go to your Destination stack, and click **Update**.

#### Step 2 - Specify stack details

Update the parameter `SendingAccounts` with the accounts you want to add (don't override the existing values, add your new accounts to the lists).
Click **Next** when you're done.

<< TODO - SCREENSHOT >>

#### Steps 3 - 4:

Click on next in steps 3-4, and check the acknowledgment checkbox, and click on **Update stack**.

<< TODO - SCREENSHOTS >>

#### Wait for the stack to be updated