variable "vpc_cidr_block" {
  description = "The CIDR block allocated to the VPC"
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr_blocks" {
  description = "The CIDR block allocations for the public subnets"
  type = "list"
  default = [
    "10.0.0.0/24",
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]
}

variable "private_subnet_cidr_blocks" {
  description = "The CIDR block allocations for the private subnets"
  type = "list"
  default = [
    "10.0.10.0/24",
    "10.0.11.0/24",
    "10.0.12.0/24"
  ]
}

resource "aws_vpc" "vpc" {
  cidr_block = "${var.vpc_cidr_block}"
}

resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_eip" "nat_eip" {
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_nat_gateway" "nat_gateway" {
  allocation_id = "${aws_eip.nat_eip.allocation_id}"
  subnet_id = ""
}

resource "aws_route_table" "public_route_table" {
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_route" "public_route" {
  route_table_id = "${aws_route_table.public_route_table.id}"
  gateway_id = "${aws_internet_gateway.internet_gateway.id}"
  destination_cidr_block = "0.0.0.0/0"
}

resource "aws_subnet" "public_subnet" {
  count = 3
  cidr_block = "${var.public_subnet_cidr_blocks[count.index]}"
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_route_table_association" "public_subnet_routes" {
  route_table_id = "${aws_route_table.public_route_table.id}"
  subnet_id = "${aws_subnet.public_subnet.*.id}"
}

resource "aws_route_table" "private_route_table" {
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_route" "private_route" {
  route_table_id = "${aws_route_table.public_route_table.id}"
  gateway_id = "${aws_internet_gateway.internet_gateway.id}"
  destination_cidr_block = "0.0.0.0/0"
}

resource "aws_subnet" "private_subnet" {
  count = 3
  cidr_block = "${var.private_subnet_cidr_blocks[count.index]}"
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_route_table_association" "private_subnet_routes" {
  route_table_id = "${aws_route_table.private_route_table.id}"
  subnet_id = "${aws_subnet.private_subnet.*.id}"
}
