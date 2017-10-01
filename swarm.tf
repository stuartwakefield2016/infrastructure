variable "coreos_owner_id" {
  description = "The AMI owner ID for CoreOS"
  default     = "595879546273"
}

variable "swarm_manager_instance_type" {
  description = "The instance type for the Swarm manager node"
  default     = "t2.micro"
}

variable "swarm_worker_instance_type" {
  description = "The instance type for the Swarm worker nodes"
  default     = "t2.micro"
}

variable "min_swarm_worker_count" {
  description = "The minimum number of Swarm workers"
  default     = 2
}

variable "max_swarm_worker_count" {
  description = "The maximum number of Swarm workers"
  default     = 9
}

variable "desired_swarm_worker_count" {
  description = "The desired number of Swarm workers"
  default     = 2
}

data "aws_ami" "coreos_ami" {
  owners      = ["${var.coreos_owner_id}"]
  most_recent = true
  filter {
    name   = "name"
    values = ["CoreOS-stable-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "template_file" "swarm_docker_tcp_service" {
  template = <<EOF
[Socket]
ListenStream=2375
BindIPv6Only=both
Service=docker.service
[Install]
WantedBy=sockets.target
EOF
}

data "template_file" "swarm_manager_service" {
  template = <<EOF
[Unit]
After=docker.service
Requires=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'docker swarm init --advertise-addr $(curl http://169.254.169.254/latest/meta-data/local-ipv4)'
[Install]
WantedBy=multi-user.target
EOF
}

data "template_file" "swarm_manager_ignition" {
  template = <<EOF
{
  "ignition":{"version":"2.0.0"},
  "systemd":{
    "units":[
      {"name":"docker.socket","enable":true},
      {"name":"containerd.service","enable":true},
      {"name":"docker.service","enable":true},
      {"name":"docker-tcp.socket","enable":true,"contents":$${swarm_docker_tcp_service}},
      {"name":"swarm-manager.service","enable":true,"contents":$${swarm_manager_service}}
    ]
  }
}
EOF
  vars {
    swarm_docker_tcp_service = "${jsonencode(data.template_file.swarm_docker_tcp_service.rendered)}"
    swarm_manager_service    = "${jsonencode(data.template_file.swarm_manager_service.rendered)}"
  }
}

data "template_file" "swarm_worker_service" {
  template = <<EOF
[Unit]
Requires=docker.service
After=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'docker swarm join --token $(docker -H $${swarm_manager_host} swarm join-token -q worker) $${swarm_manager_host}'
[Install]
WantedBy=multi-user.target
EOF
  vars {
    swarm_manager_host = "${aws_instance.swarm_manager.private_ip}"
  }
}

data "template_file" "swarm_worker_ignition" {
  template = <<EOF
{
  "ignition":{"version":"2.0.0"},
  "systemd":{
    "units":[
      {"name":"docker.socket","enable":true},
      {"name":"containerd.service","enable":true},
      {"name":"docker.service","enable":true},
      {"name":"swarm-worker.service","enable":true,"contents":$${swarm_worker_service}}
    ]
  }
}
EOF
  vars {
    swarm_worker_service = "${jsonencode(data.template_file.swarm_worker_service.rendered)}"
  }
}

resource "aws_instance" "swarm_manager" {
  ami             = "${data.aws_ami.coreos_ami.id}"
  instance_type   = "${var.swarm_manager_instance_type}"
  subnet_id       = "${aws_subnet.private_subnet.0.id}"
  user_data       = "${data.template_file.swarm_manager_ignition.rendered}"
  security_groups = [
    "${aws_security_group.swarm_manager_sg.id}",
    "${aws_security_group.swarm_node_sg.id}"
  ]
  tags {
    Name = "stuartwakefield-swarm-manager"
  }
}


resource "aws_launch_configuration" "swarm_worker" {
  name_prefix     = "stuartwakefield-swarm-worker-"
  image_id        = "${data.aws_ami.coreos_ami.id}"
  instance_type   = "${var.swarm_worker_instance_type}"
  user_data       = "${data.template_file.swarm_worker_ignition.rendered}"
  security_groups = [
    "${aws_security_group.swarm_worker_sg.id}",
    "${aws_security_group.swarm_node_sg.id}"
  ]
}

resource "aws_autoscaling_group" "swarm_worker_asg" {
  launch_configuration = "${aws_launch_configuration.swarm_worker.id}"
  min_size             = "${var.min_swarm_worker_count}"
  max_size             = "${var.max_swarm_worker_count}"
  desired_capacity     = "${var.desired_swarm_worker_count}"
  vpc_zone_identifier  = ["${aws_subnet.private_subnet.*.id}"]
  termination_policies = [
    "OldestLaunchConfiguration",
    "OldestInstance"
  ]
  tag {
    key                 = "Name"
    propagate_at_launch = true
    value               = "stuartwakefield-swarm-worker"
  }
}

resource "aws_security_group" "swarm_manager_sg" {
  vpc_id = "${aws_vpc.vpc.id}"
  tags {
    Name = "stuartwakefield-swarm-manager"
  }
}

resource "aws_security_group" "swarm_worker_sg" {
  vpc_id = "${aws_vpc.vpc.id}"
  tags {
    Name = "stuartwakefield-swarm-worker"
  }
}

resource "aws_security_group" "swarm_node_sg" {
  vpc_id = "${aws_vpc.vpc.id}"
  tags {
    Name = "stuartwakefield-swarm-node"
  }
}

output "swarm_manager_public_ip" {
  value = "${aws_instance.swarm_manager.public_ip}"
}