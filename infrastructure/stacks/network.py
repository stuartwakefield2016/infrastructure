import troposphere.ec2 as ec2
from infrastructure.core.stack import Stack
from troposphere import Ref


class NetworkStack:

    def __init__(self, prefix):
        """
        :type prefix: basestring
        :param prefix: The prefix to apply to this stack.
        """

        self._stack = Stack(prefix, "Stack")

        self._vpc = ec2.VPC(
            self._stack.component("VPC"),
            CidrBlock="10.0.0.0/16"
        )

        self._internet_gateway = ec2.InternetGateway(
            self._stack.component("InternetGateway")
        )

        self._vpc_internet_gateway_attachment = ec2.VPCGatewayAttachment(
            self._stack.component("VPCInternetGatewayAttachment"),
            InternetGatewayId=Ref(self._internet_gateway.title),
            VpcId=Ref(self._vpc.title)
        )

        # We will split the network across the two availability
        # zones for the region and have a private and a public
        # subnet. All of our application and database servers
        # and our caching proxies will sit in the private subnet.
        # Our web servers and web reverse proxies and accelerator
        # caches will sit in the public subnet.

        self._private_subnet_a = ec2.Subnet(
            self._stack.component("PrivateSubnetA"),
            AvailabilityZone="eu-west-1a",
            CidrBlock="10.0.11.0/24",
            VpcId=Ref(self._vpc.title)
        )

        self._private_subnet_b = ec2.Subnet(
            self._stack.component("PrivateSubnetB"),
            AvailabilityZone="eu-west-1b",
            CidrBlock="10.0.22.0/24",
            VpcId=Ref(self._vpc.title)
        )

        self._public_subnet_a = ec2.Subnet(
            self._stack.component("PublicSubnetA"),
            AvailabilityZone="eu-west-1a",
            CidrBlock="10.0.1.0/24",
            VpcId=Ref(self._vpc.title)
        )

        self._public_subnet_b = ec2.Subnet(
            self._stack.component("PublicSubnetB"),
            AvailabilityZone="eu-west-1b",
            CidrBlock="10.0.2.0/24",
            VpcId=Ref(self._vpc.title)
        )

        # Set up a routing table for our internet gateway

        self._internet_gateway_route_table = ec2.RouteTable(
            self._stack.component("InternetGatewayRouteTable"),
            VpcId=Ref(self._vpc.title)
        )

        # Allow outbound connections from within our subnets

        self._internet_gateway_outbound_route = ec2.Route(
            self._stack.component("InternetGatewayOutboundRoute"),
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=Ref(self._internet_gateway.title),
            RouteTableId=Ref(self._internet_gateway_route_table.title)
        )

        self._apply_resources(self._stack.template())

    def _apply_resources(self, template):
        template.add_resource([
            self._vpc,
            self._internet_gateway,
            self._vpc_internet_gateway_attachment,
            self._private_subnet_a,
            self._private_subnet_b,
            self._public_subnet_a,
            self._public_subnet_b,
            self._internet_gateway_route_table,
            self._internet_gateway_outbound_route
        ])

    def build(self):
        self._stack.build()
