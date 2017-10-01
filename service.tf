resource "aws_alb" "webapp_alb" {
  name            = "webapp-alb"
  internal        = false
  security_groups = ["${aws_security_group.webapp_alb_sg.id}"]
  subnets         = ["${aws_subnet.public_subnet.*.id}"]
}

resource "aws_alb_listener" "webapp_alb_listener" {
  "default_action" {
    target_group_arn = "${aws_alb_target_group.webapp_alb_target_group.arn}"
    type = "forward"
  }
  load_balancer_arn = "${aws_alb.webapp_alb.arn}"
  port = 80
}

resource "aws_alb_target_group" "webapp_alb_target_group" {
  port = 8000
  protocol = "HTTP"
  vpc_id = "${aws_vpc.vpc.id}"
  tags {
    Name = "stuartwakefield-webapp"
  }
}

resource "aws_autoscaling_attachment" "webapp_asg_att" {
  autoscaling_group_name = "${aws_autoscaling_group.swarm_worker_asg.id}"
  alb_target_group_arn = "${aws_alb_target_group.webapp_alb_target_group.arn}"
}

resource "aws_security_group" "webapp_alb_sg" {
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
  }
  vpc_id = "${aws_vpc.vpc.id}"
  tags {
    Name = "stuartwakefield-webapp"
  }
}